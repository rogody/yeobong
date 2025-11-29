import sys
import os 
import threading
import functools
from http.server import HTTPServer, SimpleHTTPRequestHandler 

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QMessageBox
from PySide6.QtWebEngineWidgets import QWebEngineView  
from PySide6.QtCore import QUrl


CURRENT_DIRECTORY = os.path.split(__file__)[0]
PROJECT_PATH = os.path.dirname(os.path.dirname(CURRENT_DIRECTORY))
PLY_PATH = os.path.join(PROJECT_PATH, "Resources", "point_cloud.ply")
VIEWER_FOLDER_NAME = "web_viewer"

SERVER_PORT = 8000

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
    def __init__(self):
        super().__init__()
        self.resize(1200, 1000)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. 경로 유효성 검사 (디버깅용)
        # print(f"📍 프로젝트 루트: {PROJECT_PATH}")
        # print(f"📍 PLY 경로: {PLY_PATH}")

        if not os.path.exists(PLY_PATH):
            QMessageBox.critical(self, "오류", f"PLY 파일을 찾을 수 없습니다!\n\n[탐색 경로]\n{PLY_PATH}")
            return
        
        viewer_index_path = os.path.join(PROJECT_PATH, VIEWER_FOLDER_NAME, "index.html")
        if not os.path.exists(viewer_index_path):
            QMessageBox.critical(self, "오류", f"뷰어 파일을 찾을 수 없습니다!\n\n[탐색 경로]\n{viewer_index_path}\n\n'web_viewer' 폴더가 프로젝트 최상위에 있는지 확인하세요.")
            return
        
        # 2. 서버 구동
        try:
            self.server = FileServer()
            self.server.start()
        except OSError:
            print(f"⚠️ 포트 {SERVER_PORT}가 사용 중입니다. 기존 서버를 사용합니다.")

        # 3. URL 조합 (수정됨: 전체 주소 사용)
        
        # (A) 뷰어의 주소
        viewer_url = f"http://127.0.0.1:{SERVER_PORT}/{VIEWER_FOLDER_NAME}/index.html"
        
        # (B) PLY 데이터의 '전체 URL' (이게 핵심!)
        # 상대 경로 대신 http://127.0.0.1:8000/Resources/파일명 형태로 만듭니다.
        ply_filename = os.path.basename(PLY_PATH)
        ply_full_url = f"http://127.0.0.1:{SERVER_PORT}/Resources/{ply_filename}"
        
        # (C) 최종 결합
        # load 파라미터에 전체 주소를 넣습니다.
        final_url = f"{viewer_url}?load={ply_full_url}"
        
        print(f"🔗 접속 URL: {final_url}")

        # 4. 웹 뷰어 로드
        try:
            self.browser = QWebEngineView()
            self.browser.setUrl(QUrl(final_url))
            self.layout.addWidget(self.browser)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"WebView 생성 실패:\n{e}")

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