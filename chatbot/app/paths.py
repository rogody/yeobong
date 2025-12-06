import sys
from pathlib import Path
# path settings for the app directories

def get_default_base_dir() -> Path:
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
EMBEDDING_DIR      = MODEL_DIR / "embedding"