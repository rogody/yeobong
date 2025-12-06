import os
import argparse
from pathlib import Path
import sys


import live2d.v3 as live2d
from chatbot.app import paths
from chatbot.modules.llm_model import LLModel
from chatbot.app.chatgui import MainWindow
from chatbot.core.chat_service import ChatService
from chatbot.core.prompt_builder import PromptBuilder
from chatbot.modules.RAG.factory import init_rag_components
from chatbot.modules.Emotion.emotion_model import EmotionAnalyzer   
# 감정 모델 import
from PySide6.QtWidgets import QApplication


SYS_PROMPT = """You are a chatbot that uses the provided Emotion Context about the user's feelings to respond in an empathetic, supportive, and emotionally aware way."""

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-dir",
        type=str,
        help="리소스들이 위치한 베이스 디렉토리 (옵션)",
    )
    parser.add_argument(
        "--resources-dir",
        type=str,
        help="Resources 디렉토리 경로 (옵션)",
    )
    parser.add_argument(
        "--ss-dist-dir",
        type=str,
        help="Supersplat dist 디렉토리 경로 (옵션)",
    )
    parser.add_argument(
        "--rag-dir",
        type=str,
        help="RAG 디렉토리 경로 (옵션)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    
    # 1) base-dir가 들어오면 기본 BASE_DIR 덮어쓰기
    if args.base_dir:
        paths.BASE_DIR = Path(args.base_dir)

    # 2) resources-dir / ss-dist-dir / rag-dir 덮어쓰기 또는 BASE_DIR 기준 재계산
    if args.resources_dir:
        paths.RESOURCES_DIR = Path(args.resources_dir)
    else:
        paths.RESOURCES_DIR = paths.BASE_DIR / "Resources"

    if args.ss_dist_dir:
        paths.SS_DIST_DIR = Path(args.ss_dist_dir)
    else:
        paths.SS_DIST_DIR = paths.BASE_DIR / "ss_dist"

    if args.rag_dir:
        paths.RAG_DIR = Path(args.rag_dir)
    else:
        paths.RAG_DIR = paths.BASE_DIR / "RAG"

    paths.DB_CONFIG_PATH = paths.RAG_DIR / "db_config.ini"
    

    model_name = "Qwen/Qwen3-1.7B"

    llm_client = LLModel(model_name)
    rag = init_rag_components()
    emotion_analyzer = EmotionAnalyzer()                          # 감정 model 생성

    prompt_builder = PromptBuilder(system_prompt=SYS_PROMPT)       # 감정 프롬프트 주입
        
    chat_service = ChatService(                                   
        llm_client,
        prompt_builder,
        emotion_analyzer=emotion_analyzer,                        # 감정 model 주입
        memory_store=rag.memory_store,
        memory_retriever=rag.memory_retriever,
        retrieval_top_k=rag.settings.retrieval_top_k,
    )

    # UI 실행
    app = QApplication(sys.argv)
    window = MainWindow(chat_service)
    try:
        window.show()
        exit_code = app.exec()
    finally:
        live2d.dispose()
        rag.close()
        sys.exit(exit_code)


if __name__ == "__main__":
    
    main()
