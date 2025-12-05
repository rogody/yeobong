import sys
import os 
import threading
import functools
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler 

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QMessageBox
from PySide6.QtWebEngineWidgets import QWebEngineView  
from PySide6.QtCore import QUrl


CURRENT_DIRECTORY = os.path.split(__file__)[0]
PROJECT_PATH = os.path.dirname(os.path.dirname(CURRENT_DIRECTORY))
VIEWER_FOLDER_NAME = "web_viewer"

SERVER_PORT = 8000

# 기본 리소스 경로 (필요 시 외부에서 덮어쓰기)
DEFAULT_BG_PLY = os.path.join(PROJECT_PATH, "Resources", "projply", "scene.compressed.ply")
DEFAULT_ACTOR_PLY = os.path.join(PROJECT_PATH, "Resources", "projply", "jsw.ply")

class FileServer(threading.Thread):
    """
    프로젝트 루트(MyProject) 전체를 서빙하는 로컬 서버
    """
    def __init__(self):
        super().__init__()
        self.daemon = True 
        
        # [핵심] 서버의 홈을 '프로젝트 루트'로 설정합니다.
        # 그래야 /Resources/.. 와 /web_viewer/.. 에 모두 접근 가능합니다.
        handler = functools.partial(SimpleHTTPRequestHandler, directory=PROJECT_PATH)
        
        # 주소 재사용 허용 (앱 재실행 시 포트 충돌 방지)
        self.httpd = HTTPServer(('127.0.0.1', SERVER_PORT), handler)
        self.httpd.allow_reuse_address = True

    def run(self):
        self.httpd.serve_forever()

class WebViewer(QWidget):
    """
    메인 윈도우에서 가져다 쓸 수 있는 3DGS 뷰어 위젯
    """
    def __init__(self, auto_load: bool = True):
        """
        auto_load: True면 생성 시 기본 배경+배우 PLY를 로드.
                   False면 load_scene을 호출하는 쪽에서 원하는 세트를 지정.
        """
        super().__init__()
        self.resize(1200, 1000)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self._viewer_index_path = os.path.join(PROJECT_PATH, VIEWER_FOLDER_NAME, "index.html")
        self._file_server_started = False
        self.browser = None
        self._last_camera = None
        self._load_conn = None
        self._ensure_server()
        self._init_browser()
        # 최초 로드: 배경 + 배우 기본 모델 (옵션)
        if auto_load:
            self.load_scene([DEFAULT_BG_PLY, DEFAULT_ACTOR_PLY])

    def _ensure_server(self):
        if not os.path.exists(self._viewer_index_path):
            QMessageBox.critical(self, "오류", f"뷰어 파일을 찾을 수 없습니다!\n\n[탐색 경로]\n{self._viewer_index_path}\n\n'web_viewer' 폴더가 프로젝트 최상위에 있는지 확인하세요.")
            return
        if self._file_server_started:
            return
        try:
            self.server = FileServer()
            self.server.start()
            self._file_server_started = True
        except OSError:
            # 이미 떠 있는 경우 재사용
            print(f"⚠️ 포트 {SERVER_PORT}가 사용 중입니다. 기존 서버를 사용합니다.")
            self._file_server_started = True

    def _init_browser(self):
        try:
            self.browser = QWebEngineView()
            self.layout.addWidget(self.browser)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"WebView 생성 실패:\n{e}")

    def _to_url(self, path: str) -> str:
        """
        프로젝트 루트 기준 로컬 파일 절대경로 -> 서버에서 접근 가능한 URL
        """
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
        ply_paths: 로드할 PLY 파일 경로 리스트 (배경, 배우, 감정 등)
        """
        # 현재 카메라 포즈 캐싱
        self._capture_camera()
        # 최소 하나는 있어야 로드 시도
        valid_paths = [p for p in ply_paths if p and os.path.exists(p)]
        if not valid_paths:
            QMessageBox.critical(self, "오류", "로드할 PLY 파일을 찾을 수 없습니다.\n경로를 확인하세요.")
            return
        final_url = self._build_url(valid_paths)
        print(f"🔗 접속 URL: {final_url}")
        if self.browser:
            # 기존 loadFinished 연결 해제
            if self._load_conn:
                try:
                    self.browser.loadFinished.disconnect(self._load_conn)
                except Exception:
                    pass
            self._load_conn = lambda ok: self._restore_camera(ok)
            self.browser.loadFinished.connect(self._load_conn)
            self.browser.setUrl(QUrl(final_url))

    def _capture_camera(self):
        """
        현재 카메라 포즈를 JS에서 읽어 캐싱.
        """
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
        """
        새로 로드된 뒤 이전 카메라 포즈를 복원.
        """
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

    def set_visible_emotion(self, emotion_label: str, emotion_filename_map: dict, background_patterns=None):
        """
        하나의 ssproj에 배경 + 모든 감정 PLY가 들어있는 경우,
        특정 감정 PLY만 보이게 하고 나머지는 숨긴다. 배경은 항상 표시.
        emotion_filename_map: {label: "happy.ply", ...}
        background_patterns: ["youngsin.ply", ...]
        """
        if not self.browser:
            return
        if background_patterns is None:
            background_patterns = ["youngsin.ply", "scene.compressed.ply"]

        selected = emotion_filename_map.get(emotion_label.lower()) or emotion_filename_map.get("neutral")
        if selected:
            selected = selected.lower()
        emo_files = [v.lower() for v in emotion_filename_map.values() if v]
        bg_patterns = [p.lower() for p in background_patterns if p]

        js = f"""
        (() => {{
            const selected = {json.dumps(selected or "")};
            const emoSet = new Set({json.dumps(emo_files)});
            const bgPatterns = {json.dumps(bg_patterns)};
            const et = (window.pcx?.ElementType?.splat ?? window.ElementType?.splat);
            const splats = et !== undefined ? (window.scene?.getElementsByType?.(et) || []) : [];
            splats.forEach(s => {{
                const name = (s.asset?.file?.name || s.name || "").toLowerCase();
                const isBg = bgPatterns.some(p => name.includes(p));
                if (isBg) {{
                    s.visible = true;
                    return;
                }}
                if (!emoSet.size) return;
                const isEmo = emoSet.has(name);
                if (isEmo) {{
                    s.visible = (name === selected);
                }}
            }});
        }})();
        """
        try:
            self.browser.page().runJavaScript(js)
        except Exception:
            pass

'''

class WebViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3DGS viewer(SuperSplat)")
        self.layout = QVBoxLayout()
        self.resize(1200, 1000)
        
        if not os.path.exists(PLY_PATH):
            QMessageBox.critical(self, "오류", f"파일을 찾을 수 없습니다!\n{PLY_PATH}")
            return
        
        self.server = FileServer()
        self.server.start()
        file_url = f"http://127.0.0.1:{SERVER_PORT}/{self.server.file_name}"
        target_url = f"https://superspl.at/editor?load={file_url}"
        
        try:
            self.browser = QWebEngineView()
            self.browser.setUrl(QUrl(target_url))
            self.layout.addWidget(self.browser)
            self.setLayout(self.layout)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"웹 엔진 로드 실패:\n{e}")
        
        
'''
