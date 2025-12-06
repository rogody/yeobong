'''
Data types used in the chatbot application.
'''
from dataclasses import dataclass
@dataclass
class ChatResult:
    reply: str
    emotion : str

