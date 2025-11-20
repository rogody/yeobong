from chatbot.modules.llm_model import LLModel
from chatbot.app.ui import ChatUI
from chatbot.app.controller import ChatController
from chatbot.core.chat_service import ChatService
from chatbot.core.prompt_builder import PromptBuilder
from RAG.factory import init_rag_components
from Emotion.emotion_model import EmotionAnalyzer                 # 감정 모델 import


def main():
    model_name = "Qwen/Qwen3-1.7B"

    llm_client = LLModel(model_name)
    rag = init_rag_components()
    emotion_analyzer = EmotionAnalyzer()                          # 감정 model 생성

    prompt_builder = PromptBuilder(system_prompt= "You are a chatbot that uses the provided Emotion Context "
                                    "about the user's feelings to respond in an empathetic, supportive, "
                                    "and emotionally aware way."  # 감정 프롬프트 주입
                                )       
    chat_service = ChatService(                                   
        llm_client,
        prompt_builder,
        emotion_analyzer=emotion_analyzer,                        # 감정 model 주입
        memory_store=rag.memory_store,
        memory_retriever=rag.memory_retriever,
        retrieval_top_k=rag.settings.retrieval_top_k,
    )
    chat_controller = ChatController(chat_service)

    ui = ChatUI(chat_controller)
    try:
        ui.run()
    finally:
        rag.close()


if __name__ == "__main__":
    main()
