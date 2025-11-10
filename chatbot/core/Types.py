'''
사용하는 자료형들을 정의
example
class Pad
    pleasure: float
    arousal: float
    dominance: float
    
class Persona, class Episodicmemory 등등
    
'''
from dataclasses import dataclass
@dataclass
class ChatResult:
    reply: str