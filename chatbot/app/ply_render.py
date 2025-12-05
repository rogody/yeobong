import sys
import os
import threading
import functools
from http.server import HTTPServer, SimpleHTTPRequestHandler

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QMessageBox
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl


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
        final_url = self._build_url(valid_paths)
        print(f"📦 로드 URL: {final_url}")
        if self.browser:
            if self._load_conn:
                try:
                    self.browser.loadFinished.disconnect(self._load_conn)
                except Exception:
                    pass
            self._load_conn = lambda ok: self._restore_camera(ok)
            self.browser.loadFinished.connect(self._load_conn)
            self.browser.setUrl(QUrl(final_url))

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
