'''
프롬프트 생성
ex> pad, rag등으로 부터 모은 정보를 총합해서 프롬프트 조립
'''

class PromptBuilder:
    def __init__(self, system_prompt: str = "you are user's chat bot assistance. Don't generate answers that aren't related to the user's input. user: "):
        self.system_prompt = system_prompt
    
    #create prompt
    def build(self, user_input: str) -> str: #add other parameters later
        prompt=self.system_prompt+user_input
        return prompt