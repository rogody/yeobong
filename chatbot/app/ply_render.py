import sys
import os
import json
import threading
import functools
from http.server import HTTPServer, SimpleHTTPRequestHandler

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QMessageBox
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QTimer


CURRENT_DIRECTORY = os.path.split(__file__)[0]
PROJECT_PATH = os.path.dirname(os.path.dirname(CURRENT_DIRECTORY))
VIEWER_FOLDER_NAME = "web_viewer"

SERVER_PORT = 8000
# 기본 카메라 초기 위치/타겟 (뷰어 기본값에 가깝게 되돌림)
DEFAULT_CAMERA_POS = (0.0, 1.6, 3.0)
DEFAULT_CAMERA_TARGET = (0.0, 1.2, 0.0)

# 기본 리소스 경로 (사용하지 않는 기본값, auto_load=False에서 무시됨)
DEFAULT_BG_PLY = os.path.join(PROJECT_PATH, "Resources", "projply", "youngsin.ply")
DEFAULT_ACTOR_PLY = os.path.join(PROJECT_PATH, "Resources", "projply", "jsw.ply")


class FileServer(threading.Thread):
    """
    로컬 루트(MyProject) 전체를 서빙하는 HTTP 서버
    """
    def __init__(self):
        super().__init__()
        self.daemon = True
        handler = functools.partial(SimpleHTTPRequestHandler, directory=PROJECT_PATH)
        self.httpd = HTTPServer(('127.0.0.1', SERVER_PORT), handler)
        self.httpd.allow_reuse_address = True

    def run(self):
        self.httpd.serve_forever()


class WebViewer(QWidget):
    """
    메인 윈도우 안에 임베드된 3DGS 뷰어
    """
    def __init__(self, auto_load: bool = True):
        super().__init__()
        self.resize(1200, 1000)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self._viewer_index_path = os.path.join(PROJECT_PATH, VIEWER_FOLDER_NAME, "index.html")
        self._file_server_started = False
        self.browser = None
        self._last_camera = None
        self._load_conn = None
        self._scene_ready = False
        self._pending_visibility = None
        self._loaded_names = set()
        self._visibility_retries = 0
        self._pending_grid = None
        self._pending_bg = None
        self._view_retry = 0
        self._camera_initialized = False
        self._camera_retry = 0
        self._default_grid_visible = False
        self._default_bg_color = (0.97, 0.97, 0.97, 1.0)
        self.base_filename = os.path.basename(DEFAULT_BG_PLY).lower()
        self.neutral_filename = os.path.basename(DEFAULT_ACTOR_PLY).lower()
        self._ensure_server()
        self._init_browser()
        if auto_load:
            self.load_scene([DEFAULT_BG_PLY, DEFAULT_ACTOR_PLY])

    def _ensure_server(self):
        if not os.path.exists(self._viewer_index_path):
            QMessageBox.critical(self, "오류", f"뷰어 파일을 찾을 수 없습니다!\n\n[경로]\n{self._viewer_index_path}\n\n'web_viewer' 폴더가 프로젝트 루트에 있는지 확인해주세요.")
            return
        if self._file_server_started:
            return
        try:
            self.server = FileServer()
            self.server.start()
            self._file_server_started = True
        except OSError:
            print(f"⚠️ 포트 {SERVER_PORT}가 사용 중입니다. 기존 서버를 사용합니다.")
            self._file_server_started = True

    def _init_browser(self):
        try:
            self.browser = QWebEngineView()
            self.layout.addWidget(self.browser)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"WebView 생성 실패:\n{e}")

    def _to_url(self, path: str) -> str:
        rel_path = os.path.relpath(path, PROJECT_PATH).replace("\\", "/")
        return f"http://127.0.0.1:{SERVER_PORT}/{rel_path}"

    def _build_url(self, ply_paths):
        viewer_url = f"http://127.0.0.1:{SERVER_PORT}/{VIEWER_FOLDER_NAME}/index.html"
        load_params = []
        for p in ply_paths:
            if p and os.path.exists(p):
                load_params.append(f"load={self._to_url(p)}")
        query = "&".join(load_params)
        return f"{viewer_url}?{query}"

    def load_scene(self, ply_paths):
        """
        ply_paths: 로드할 PLY 파일 경로 리스트 (배경, 배우/감정)
        """
        self._capture_camera()
        valid_paths = [p for p in ply_paths if p and os.path.exists(p)]
        if not valid_paths:
            QMessageBox.critical(self, "오류", "로드할 PLY 파일을 찾을 수 없습니다.\n경로를 확인해주세요.")
            return
        self._scene_ready = False
        self._loaded_names = {os.path.basename(p).lower() for p in valid_paths}
        final_url = self._build_url(valid_paths)
        print(f"📦 로드 URL: {final_url}")
        if self.browser:
            if self._load_conn:
                try:
                    self.browser.loadFinished.disconnect(self._load_conn)
                except Exception:
                    pass
            def _on_loaded(ok):
                self._scene_ready = bool(ok)
                # restore previous camera if we have one
                if self._last_camera:
                    self._restore_camera(ok)
                self._apply_pending_visibility()
                # 기본 뷰 세팅도 로딩 완료 후 바로 적용
                if self._pending_grid is None:
                    self._pending_grid = self._default_grid_visible
                if self._pending_bg is None:
                    self._pending_bg = self._default_bg_color
                self._apply_pending_view_settings()
            self._load_conn = _on_loaded
            self.browser.loadFinished.connect(self._load_conn)
            self.browser.setUrl(QUrl(final_url))

    def preload_scene(self, ply_paths, initial_visible=None, always_visible=None, fallback_name=None):
        """
        Load PLYs once and optionally queue which ones stay visible after load.
        """
        self.load_scene(ply_paths)
        if initial_visible:
            self.set_visibility(initial_visible, always_visible=always_visible, fallback_name=fallback_name)

    def _capture_camera(self):
        if not self.browser:
            return
        js = """
            (() => {
                const c = window.scene?.camera;
                if (!c) return null;
                const p = c.getPosition();
                const t = c.getTarget();
                return { p: [p.x, p.y, p.z], t: [t.x, t.y, t.z] };
            })();
        """
        try:
            self.browser.page().runJavaScript(js, lambda result: setattr(self, "_last_camera", result))
        except Exception:
            pass

    def _restore_camera(self, ok):
        if not ok or not self.browser or not self._last_camera:
            return
        pose = self._last_camera
        try:
            p = pose.get("p")
            t = pose.get("t")
            if not p or not t:
                return
            js = f"""
                (() => {{
                    const c = window.scene?.camera;
                    if (!c) return;
                    c.setPosition({p[0]}, {p[1]}, {p[2]});
                    c.setTarget({t[0]}, {t[1]}, {t[2]});
                }})();
            """
            self.browser.page().runJavaScript(js)
        except Exception:
            pass

    def set_visibility(self, visible_names, always_visible=None, fallback_name=None):
        """
        visible_names: iterable of filenames to set visible (case-insensitive).
        always_visible: iterable kept visible regardless (e.g., background).
        fallback_name: filename to force visible when emotion ply is missing.
        """
        names = set(n.lower() for n in visible_names if n)
        if always_visible:
            names.update(n.lower() for n in always_visible if n)
        else:
            names.add(self.base_filename)
        if fallback_name:
            names.add(fallback_name.lower())
        if not names:
            return False
        self._pending_visibility = sorted(names)
        self._visibility_retries = 0
        self._apply_pending_visibility()
        self._schedule_visibility_retry()
        return True

    def set_overlay(self, enabled: bool):
        """
        Toggle camera overlay (e.g., Gaussian helpers) on/off in the viewer.
        """
        if not self.browser:
            return False
        flag = "true" if enabled else "false"
        js = f"""
            (() => {{
                const scene = window.scene;
                if (!scene || !scene.events || !scene.events.fire) return null;
                scene.events.fire('camera.setOverlay', {flag});
                return scene.events.invoke ? scene.events.invoke('camera.overlay') : null;
            }})();
        """
        try:
            self.browser.page().runJavaScript(js)
            return True
        except Exception:
            return False

    def set_grid(self, enabled: bool):
        """
        Toggle ground grid visibility.
        """
        self._pending_grid = bool(enabled)
        print(f"[VIEW_SETTINGS] set_grid called -> {self._pending_grid}")
        return self._apply_pending_view_settings()

    def set_background(self, r: float = 1.0, g: float = 1.0, b: float = 1.0, a: float = 1.0):
        """
        Set background color (0-1 range). Defaults to white.
        """
        self._pending_bg = (float(r), float(g), float(b), float(a))
        print(f"[VIEW_SETTINGS] set_background called -> {self._pending_bg}")
        return self._apply_pending_view_settings()

    def _apply_pending_view_settings(self):
        """
        Apply grid/background once scene/events are ready. Retries a few times if not ready.
        """
        print(f"[VIEW_SETTINGS] apply_pending_view_settings start ready={self._scene_ready} pending_grid={self._pending_grid} pending_bg={self._pending_bg}")
        if not self.browser or not self._scene_ready:
            print(f"[VIEW_SETTINGS] scene not ready yet (browser={bool(self.browser)}, ready={self._scene_ready}) pending_grid={self._pending_grid} pending_bg={self._pending_bg}")
            self._schedule_view_retry()
            return False
        self._view_retry = 0
        applied_any = False
        try:
            grid_val = self._pending_grid
            bg_val = self._pending_bg
            if grid_val is None and bg_val is None:
                return False
            js = """
                (() => {
                    const scene = window.scene;
                    if (!scene?.events?.fire) return { ok:false, reason:'no-events' };
                    if (!scene.grid) return { ok:false, reason:'no-grid' };
                    const res = { ok:true };
                    if (__GRID__ !== null) {
                        scene.events.fire('grid.setVisible', !!__GRID__);
                        res.grid = scene.events.invoke ? scene.events.invoke('grid.visible') : !!__GRID__;
                    }
                    if (__BG__ !== null) {
                        const [r,g,b,a] = __BG__;
                        try {
                            const clr = new Color(r,g,b,a);
                            scene.events.fire('setBgClr', clr);
                            res.bg = { r: clr.r, g: clr.g, b: clr.b, a: clr.a };
                        } catch (e) {
                            res.bg = { error: String(e) };
                        }
                    }
                    return res;
                })();
            """
            js = js.replace("__GRID__", "true" if grid_val else "false" if grid_val is not None else "null")
            js = js.replace("__BG__", "null" if bg_val is None else f"[{bg_val[0]}, {bg_val[1]}, {bg_val[2]}, {bg_val[3]}]")
            self.browser.page().runJavaScript(js, lambda res: print(f"[VIEW_SETTINGS] applied grid={grid_val} bg={bg_val} -> {res}"))
            applied_any = True
            self._pending_grid = None
            self._pending_bg = None
        except Exception as exc:
            print(f"[VIEW_SETTINGS] apply failed: {exc}")
            self._schedule_view_retry()
            return False
        return applied_any

    def _schedule_view_retry(self):
        if self._view_retry >= 20:
            return
        self._view_retry += 1
        print(f"[VIEW_SETTINGS] retry {self._view_retry} pending_grid={self._pending_grid} pending_bg={self._pending_bg}")
        QTimer.singleShot(300, self._apply_pending_view_settings)

    def _set_initial_camera(self, yaw_deg: float = 60.0, height_offset: float = 10.0):
        """
        Rotate camera left by yaw_deg around current target and raise height by height_offset.
        """
        if not self.browser:
            return False
        js = f"""
            (() => {{
                const scene = window.scene;
                const cam = scene?.camera;
                if (!cam || !cam.entity) return null;
                // pick first splat center as target if available
                let target = cam.focalPoint ? {{ ...cam.focalPoint }} : {{ x: 0, y: 0, z: 0 }};
                const splats = scene.getElementsByType ? scene.getElementsByType('splat') : [];
                if (splats && splats.length > 0) {{
                    const b = splats[0].worldBound;
                    if (b) target = {{ x: b.center.x, y: b.center.y, z: b.center.z }};
                }}
                const tx = target.x ?? 0, ty = target.y ?? 0, tz = target.z ?? 0;
                const pos = cam.entity.getPosition();
                const dx = pos.x - tx;
                const dz = pos.z - tz;
                const r = Math.hypot(dx, dz) || 3.0;
                const baseAngle = Math.atan2(dz, dx);
                const ang = baseAngle + ({yaw_deg} * Math.PI / 180);
                const nx = tx + r * Math.cos(ang);
                const nz = tz + r * Math.sin(ang);
                const ny = pos.y + ({height_offset});
                cam.setPose({{ x: nx, y: ny, z: nz }}, {{ x: tx, y: ty, z: tz }}, 1);
                return {{ pos: [nx, ny, nz], target: [tx, ty, tz], r, ang, splatCount: splats?.length ?? 0 }};
            }})();
        """
        try:
            self.browser.page().runJavaScript(js)
            return True
        except Exception:
            return False

    def _apply_initial_camera(self):
        # Try immediately, then a few retries as splats finish importing.
        if self._camera_initialized:
            return
        success = self._set_initial_camera(yaw_deg=60.0, height_offset=10.0)
        if success:
            self._camera_initialized = True
            return
        if self._camera_retry >= 10:
            return
        self._camera_retry += 1
        QTimer.singleShot(400, self._apply_initial_camera)

    def _schedule_visibility_retry(self):
        if self._visibility_retries >= 20:
            return
        self._visibility_retries += 1
        QTimer.singleShot(300, self._retry_visibility_once)

    def _retry_visibility_once(self):
        self._apply_pending_visibility()
        self._schedule_visibility_retry()

    def _apply_pending_visibility(self):
        if not self.browser or not self._pending_visibility or not self._scene_ready:
            return False
        visible_json = json.dumps(self._pending_visibility)
        js = f"""
            (() => {{
                const visible = new Set({visible_json});
                const apply = () => {{
                    const scene = window.scene;
                    if (!scene || !scene.getElementsByType) return null;
                    const list = scene.getElementsByType('splat') || [];
                    if (!list.length) {{
                        setTimeout(apply, 50);
                        return null;
                    }}
                    const visibleNow = [];
                    const allNames = [];
                    list.forEach((s) => {{
                        const name = (s.filename || s.name || '').toLowerCase();
                        allNames.push(name);
                        const isVisible = visible.has(name);
                        s.visible = isVisible;
                        if (isVisible) visibleNow.push(name);
                    }});
                    return {{
                        total: list.length,
                        visible: visibleNow,
                        all: allNames,
                    }};
                }};
                return apply();
            }})();
        """
        try:
            def _log(result):
                print(f"[PLY_VIS] target={self._pending_visibility} result={result}")
            self.browser.page().runJavaScript(js, _log)
            return True
        except Exception:
            return False
