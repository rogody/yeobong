"""
프롬프트 생성
향후 PAD/RAG/감정 등 여러 정보를 조합해 확장할 수 있도록 설계.
"""

from __future__ import annotations

from typing import Optional


class PromptBuilder:
    def __init__(self, system_prompt: str = ""):
        self.system_prompt = system_prompt.strip()

    def build(self, user_input: str, context: Optional[str] = None) -> str:
        """시스템 프롬프트 + RAG 문맥 + 사용자 입력을 하나로 합칩니다."""
        segments = []
        if self.system_prompt:
            segments.append(f"System:\n{self.system_prompt}")
        if context:
            segments.append(f"Context:\n{context}")
        segments.append(f"User:\n{user_input}")
        return "\n\n".join(segments)
