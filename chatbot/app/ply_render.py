
import os 
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler 

from PySide6.QtWidgets import QVBoxLayout, QWidget, QMessageBox
from PySide6.QtWebEngineWidgets import QWebEngineView  
from PySide6.QtCore import QUrl


CURRENT_DIRECTORY = os.path.split(__file__)[0]
PROJECT_PATH = os.path.dirname(os.path.dirname(CURRENT_DIRECTORY))
PLY_PATH = os.path.join(PROJECT_PATH, "Resources", "jsw2", "point_cloud", "iteration_7000", "point_cloud.ply")
VIEWER_FOLDER_NAME = "ss_dist"

SERVER_PORT = 8000

def SimpleHttp(*args):
    return SimpleHTTPRequestHandler(*args, directory=PROJECT_PATH)

class FileServer(threading.Thread):
    
    #create local server for serving 3DGS viewer and PLY files
    def __init__(self):
        super().__init__()
        self.daemon = True 
        
        self.httpd = HTTPServer(('127.0.0.1', SERVER_PORT), SimpleHttp)
        self.httpd.allow_reuse_address = True

    def run(self):
        self.httpd.serve_forever()




class WebViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(1200, 1000)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        if not os.path.exists(PLY_PATH):
            print("no ply file in the path: ", PLY_PATH)
            return
        
        viewer_index_path = os.path.join(PROJECT_PATH, VIEWER_FOLDER_NAME, "index.html")
        if not os.path.exists(viewer_index_path):
            print("can't find the supersplat viewer in the path: ", viewer_index_path)
            return
    
        try:
            self.server = FileServer()
            self.server.start()
        except OSError:
            print(f"port", SERVER_PORT, "is already in use.")
            return
            

        viewer_url = f"http://127.0.0.1:{SERVER_PORT}/{VIEWER_FOLDER_NAME}/index.html"
        
        relative_path = os.path.relpath(PLY_PATH, PROJECT_PATH) #상대 경로로 설정 
        relative_path = relative_path.replace(os.sep, '/')
        ply_full_url = f"http://127.0.0.1:{SERVER_PORT}/{relative_path}"
        
        final_url = f"{viewer_url}?load={ply_full_url}"
        
        print("Loading 3DGS viewer from URL:", final_url)

        # 4. 웹 뷰어 로드
        try:
            self.browser = QWebEngineView()
            self.browser.setUrl(QUrl(final_url))
            self.layout.addWidget(self.browser)
        except Exception as e:
            QMessageBox.critical(self, "Error", "failed to create WebView:\n", str(e))

