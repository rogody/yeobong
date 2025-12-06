import sys
from pathlib import Path


def get_default_base_dir() -> Path:
    """
    개발 환경(.py) + PyInstaller 실행파일(.exe)에서 공통으로 사용할 기본 BASE_DIR.
    - .py로 실행할 때: 현재 파일 기준으로 프로젝트 루트
    - exe로 실행할 때: exe가 위치한 폴더
    """
    if getattr(sys, "frozen", False):
        # PyInstaller로 빌드된 실행 파일인 경우
        return Path(sys.executable).parent
    else:
        # 예: yeobong/chatbot/app/paths.py 라고 가정하면,
        # parent.parent.parent 가 yeobong 루트
        return Path(__file__).resolve().parent.parent.parent


# 기본 BASE_DIR 계산
BASE_DIR: Path = get_default_base_dir()

# 프로젝트 구조에 맞춰 필요한 경로들 정의 (필요 없는 건 빼도 됨)
RESOURCES_DIR      = BASE_DIR / "Resources"
PLY_DIR            = RESOURCES_DIR / "projply"
MODEL_DIR          = BASE_DIR / "model"         
SS_DIST_DIR        = BASE_DIR / "ss_dist"   
RAG_DIR            = BASE_DIR / "RAG"
DB_CONFIG_PATH     = RAG_DIR / "db_config.ini"
LOG_DIR            = BASE_DIR / "logs"