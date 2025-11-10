import customtkinter as ctk
from tkinter import END

from chatbot.modules.llm_model import LLModel
from .controller import ChatController

class ChatUI:
    """
    아주 간단한 CustomTkinter 기반 챗 UI.
    """

    def __init__(self, controller: ChatController):
        self.controller = controller  
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("AI chat bot")
        self.root.geometry("800x600")
        
        # chat area
        self.chat_area = ctk.CTkTextbox(self.root, wrap="word")
        self.chat_area.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        self.chat_area.configure(state="disabled")
        
        # bottom area
        bottom_frame = ctk.CTkFrame(self.root)
        bottom_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        # user input
        self.input_entry = ctk.CTkEntry(bottom_frame, placeholder_text="메시지를 입력하고 Enter 또는 Send를 누르세요.")
        self.input_entry.pack(side="left", fill="x", expand=True, padx=10)
        self.input_entry.bind("<Return>", self.send_event) # Enter 키로도 전송

        # send button 
        self.send_button = ctk.CTkButton(bottom_frame, text="Send", command=self.on_send)
        self.send_button.pack(side="right")

        self.append_message("system", "YEOBONG")

    def append_message(self, speaker: str, text: str):
        """채팅창에 메시지를 추가하는 헬퍼."""
        self.chat_area.configure(state="normal")
        if speaker == "user":
            prefix = "You: "
        elif speaker == "bot":
            prefix = "Bot: "
        else:
            prefix = ""

        self.chat_area.insert("end", prefix + text + "\n")
        self.chat_area.see("end")
        self.chat_area.configure(state="disabled")

    def send_event(self, event):
        self.on_send()
    
    def on_send(self):
        user_text = self.input_entry.get().strip()
        if not user_text:
            return

        # 입력창 비우기
        self.input_entry.delete(0, END)

        # 유저 메시지 출력
        self.append_message("user", user_text)

        # 버튼/입력 잠깐 비활성화 (모델이 느릴 수 있어서)
        self.send_button.configure(state="disabled")
        self.input_entry.configure(state="disabled")
        self.root.update_idletasks()

        '''
        try:
            # 지금은 user_id 하나만 쓴다고 가정
            reply = self.controller.handle_user_message(user_id="user1", text=user_text)
        except Exception as e:
            reply = f"(에러 발생: {e})"
            '''
            
        #reply = self.controller.handle_user_message(user_id="user1", text=user_text)
        reply = self.controller.handle_user_message(text=user_text)

        # 봇 응답 출력
        self.append_message("bot", reply)

        # 다시 입력 가능하게
        self.send_button.configure(state="normal")
        self.input_entry.configure(state="normal")
        self.input_entry.focus()

    def run(self):
        self.root.mainloop()


