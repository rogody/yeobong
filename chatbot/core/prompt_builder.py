"""
PAD/RAG/감정 등 여러 정보를 조합해 프롬프트 생성, 확장할 수 있도록 설계.
"""

from __future__ import annotations

from typing import Optional


class PromptBuilder:
    def __init__(self, system_prompt: str = "You are a user's chatbot assistant."):
        self.system_prompt = system_prompt.strip()

    def build(
        self, 
        user_input: str, 
        context: Optional[str] = None,
        emotion_context: Optional[str] = None,
        long_emotion_summary: Optional[str] = None,
        
        ) -> str:
        """시스템 프롬프트 + RAG 문맥 + 발화의 감정 정보 + 사용자 입력 합치기"""
        segments = []
        if self.system_prompt:
            segments.append(f"System:\n{self.system_prompt}")
        if context:
            segments.append(f"Context:\n{context}")
        if emotion_context:
            segments.append(f"Emotion Context:\n{emotion_context}")
            print("emotion:"+emotion_context)
        if long_emotion_summary:
            segments.append(f"Long-term summary:\n{long_emotion_summary}")
            print("long-term summary: "+long_emotion_summary)
        
        segments.append(f"User:\n{user_input}")
        return "\n\n".join(segments)
