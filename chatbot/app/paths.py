import sys
from pathlib import Path


def get_default_base_dir() -> Path:
    """
    개발 환경(.py) + PyInstaller 실행파일(.exe)에서 공통으로 사용할 기본 BASE_DIR.
    - .py로 실행할 때: 현재 파일 기준으로 프로젝트 루트
    - exe로 실행할 때: exe가 위치한 폴더
    """
    if getattr(sys, "frozen", False):
        #if it is a execution file
        return Path(sys.executable).parent
    else:
        return Path(__file__).resolve().parent.parent.parent


BASE_DIR: Path = get_default_base_dir()

RESOURCES_DIR      = BASE_DIR / "Resources"
PLY_DIR            = RESOURCES_DIR / "projply"
MODEL_DIR          = BASE_DIR / "model"         
SS_DIST_DIR        = BASE_DIR / "ss_dist"   
RAG_DIR            = BASE_DIR / "RAG"
