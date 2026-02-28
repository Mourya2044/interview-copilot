from dataclasses import dataclass
from typing import Literal

Action = Literal[
    "respond",
    "wait",
    "ignore",
]

@dataclass
class ClassificationResult:
    intent: str
    action: Action
    confidence: float
    reasoning: str
