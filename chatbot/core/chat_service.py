
#module에서 구현한 것들을 사용하여 prompt 생성 -> llm으로 답변 생성 -> 저장 -> 답변 반환
from chatbot.modules.llm_model import LLModel
from chatbot.core.Types import ChatResult
from chatbot.core.prompt_builder import PromptBuilder

class ChatService:
    def __init__(self, llm: LLModel, prompt_builder: PromptBuilder):
        self.llm = llm
        self.pb = prompt_builder
        
    def run_turn(self, user_input:str) -> ChatResult:
        
        '''
        rag
        lora
        emotion
        등등
        '''
        prompt = self.pb.build(user_input)
        reply = self.llm.generate(prompt)
        
  
        # 히스토리에 이번 턴 추가
        self.recent_turns.append(("user", user_input))
        self.recent_turns.append(("assistant", reply))
        # 너무 길어지면 요약 갱신
        if len(self.recent_turns) > self.max_recent_turns:
            self._update_long_emotion_summary()
       

        self._persist_message("user", user_input)
        self._persist_message("assistant", reply)

        return ChatResult(reply=reply)

    #emotion
    def _build_emotion_context(self, user_input: str) -> Optional[str]:
        # EmotionAnalyzer가 아직 없으면 그냥 건너뜀
        if not hasattr(self, "emotion_analyzer") or self.emotion_analyzer is None:
            return None

        try:
            result = self.emotion_analyzer.analyze(user_input)
        except Exception as exc:
            logging.warning("Emotion analysis failed: %s", exc)
            return None

        if not result:
            return None

        # 결과를 리스트 형태로 통일
        if isinstance(result, dict):
            emo_list = [result]
        else:
            emo_list = result

        # label/score 있는 것만 추리고 score 내림차순 정렬
        emo_list = [
            r for r in emo_list
            if isinstance(r, dict) and "label" in r and "score" in r
        ]
        if not emo_list:
            return None

        emo_list.sort(key=lambda r: r["score"], reverse=True)
        top = emo_list[0]

        # LLM 프롬프트에 넣을 감정 컨텍스트 문자열 생성
        lines = ["Emotion:"]
        lines.append(f"- primary: {top['label']} ({top['score']:.2f})")
        for r in emo_list[1:3]:  # 원하면 상위 2개 정도 더
            lines.append(f"- {r['label']}: {r['score']:.2f}")

        return "\n".join(lines)
   
    def _update_long_emotion_summary(self) -> None:
        if not self.recent_turns:
            return

        convo_lines = []
        for speaker, text in self.recent_turns:
            role = "User" if speaker == "user" else "Assistant"
            convo_lines.append(f"{role}: {text}")
        convo_text = "\n".join(convo_lines)

        prompt = (
            "You maintain a running summary of the conversation, "
            "with a focus on the user's long-term emotional state.\n\n"
            f"Existing summary:\n{self.long_emotion_summary or '(none yet)'}\n\n"
            f"New turns:\n{convo_text}\n\n"
            "Update the summary in under 200 words."
        )
        new_summary = self.llm.generate(prompt)
        self.long_emotion_summary = new_summary.strip()
        self.recent_turns.clear()
    #emotion

    def _build_context(self, user_input: str) -> Optional[str]:
        if not self.memory_retriever:
            return None
        try:
            chunks = self.memory_retriever.search(user_input, top_k=self.retrieval_top_k)
        except Exception as exc:
            logging.warning("Memory retrieval failed: %s", exc)
            return None
        if not chunks:
            return None

        formatted = []
        for row in chunks:
            snippet = row.get("chunk_text", "").strip()
            if not snippet:
                continue
            prefix = f"conv={row.get('conv_id')} msg={row.get('msg_id')} ord={row.get('ord')}"
            formatted.append(f"[{prefix}] {snippet}")
        return "\n".join(formatted) if formatted else None

    def _persist_message(self, author_kind: str, content: str) -> None:
        if not self.memory_store or not self.conv_id:
            return
        clean = self._strip_think(content)
        if not clean:
            return
        try:
            self.memory_store.save_with_embedding(
                conv_id=self.conv_id,
                author_kind=author_kind,
                content=clean,
            )
        except Exception as exc:
            logging.warning("Failed to persist %s message: %s", author_kind, exc)

    def close_session(self) -> None:
        if not self.memory_store or not self.conv_id:
            return
        try:
            self.memory_store.delete_conversation(self.conv_id)
        except Exception as exc:
            logging.warning("Failed to delete conversation %s: %s", self.conv_id, exc)
        finally:
            self.conv_id = None

    def _strip_think(self, text: Optional[str]) -> str:
        if not text:
            return ""
        cleaned = self._think_pattern.sub("", text)
        return cleaned.strip()
