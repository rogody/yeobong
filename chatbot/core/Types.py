'''
Data types used in the chatbot application.
it can be extended with more fields as needed.
    
'''
from dataclasses import dataclass
@dataclass
class ChatResult:
    reply: str
    emotion : str

