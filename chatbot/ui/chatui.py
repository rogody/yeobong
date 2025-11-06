import customtkinter as ctk
from tkinter import END

from chatbot.infra.llm_model import LLModel

class ChatUI:
    """
    아주 간단한 CustomTkinter 기반 챗 UI.
    지금은 엔진 없이 QwenHFClient를 직접 사용한다.
    나중에 ConversationApp으로 갈아끼우기 쉽게
    backend.generate_reply(user_id, text) 인터페이스만 맞춰두자.
    """

    def __init__(self, backend):
        self.backend = backend  # backend는 generate_reply(user_id, text) 메서드를 가지고 있다고 가정

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("AI Memory Bot (Qwen 4B Demo)")
        self.root.geometry("800x600")

        # 상단 채팅 출력 영역
        self.chat_box = ctk.CTkTextbox(self.root, wrap="word", state="disabled")
        self.chat_box.pack(fill="both", expand=True, padx=10, pady=10)

        # 하단 입력 + 버튼 프레임
        bottom_frame = ctk.CTkFrame(self.root)
        bottom_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.input_entry = ctk.CTkEntry(bottom_frame, placeholder_text="메시지를 입력하고 Enter 또는 Send를 누르세요.")
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.input_entry.bind("<Return>", self.on_send_event)  # Enter 키로도 전송

        self.send_button = ctk.CTkButton(bottom_frame, text="Send", command=self.on_send)
        self.send_button.pack(side="right")

        # 초기 안내 메시지
        self._append_message("system", "Qwen 4B 기반 데모 챗봇입니다. 아무 말이나 해보세요!")

    def _append_message(self, speaker: str, text: str):
        """채팅창에 메시지를 추가하는 헬퍼."""
        self.chat_box.configure(state="normal")
        if speaker == "user":
            prefix = "You: "
        elif speaker == "bot":
            prefix = "Bot: "
        else:
            prefix = ""

        self.chat_box.insert(END, prefix + text + "\n")
        self.chat_box.see(END)
        self.chat_box.configure(state="disabled")

    def on_send_event(self, event):
        self.on_send()

    def on_send(self):
        user_text = self.input_entry.get().strip()
        if not user_text:
            return

        # 입력창 비우기
        self.input_entry.delete(0, END)

        # 유저 메시지 출력
        self._append_message("user", user_text)

        # 버튼/입력 잠깐 비활성화 (모델이 느릴 수 있어서)
        self.send_button.configure(state="disabled")
        self.input_entry.configure(state="disabled")
        self.root.update_idletasks()

        try:
            # 지금은 user_id 하나만 쓴다고 가정
            reply = self.backend.generate_reply(user_id="user1", text=user_text)
        except Exception as e:
            reply = f"(에러 발생: {e})"

        # 봇 응답 출력
        self._append_message("bot", reply)

        # 다시 입력 가능하게
        self.send_button.configure(state="normal")
        self.input_entry.configure(state="normal")
        self.input_entry.focus()

    def run(self):
        self.root.mainloop()


class SimpleLLMBackend:
    """
    나중에 ConversationApp을 붙이기 전에 쓰는 간단 백엔드.
    - generate_reply(user_id, text) -> str
    내부에서는 QwenHFClient를 직접 호출한다.
    """

    def __init__(self, llm_client: LLModel):
        self.llm = llm_client

    def generate_reply(self, user_id: str, text: str) -> str:
        # 지금은 user_id는 무시하고, 프롬프트에 그대로 text만 넣는다.
        return self.llm.generate(text, max_new_tokens=256)