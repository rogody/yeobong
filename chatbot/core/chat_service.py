
#module에서 구현한 것들을 사용하여 prompt 생성 -> llm으로 답변 생성 -> 저장 -> 답변 반환
from chatbot.modules.llm_model import LLModel
from chatbot.core.types import ChatResult
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
        #결과 저장
        result = ChatResult(reply = reply)
        return result
        