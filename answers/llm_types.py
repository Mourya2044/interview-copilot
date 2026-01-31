from dataclasses import dataclass
from typing import Literal

LLMMode = Literal["concise", "detailed"]

@dataclass
class LLMAnswer:
    text: str
    mode: LLMMode
    confidence: float
