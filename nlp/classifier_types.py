from dataclasses import dataclass
from typing import Literal

Intent = Literal[
    "behavioral",
    "algorithmic",
    "system_design",
    "clarification",
    "filler",
    "unknown",
]

Action = Literal[
    "respond",
    "wait",
    "ignore",
]

@dataclass
class ClassificationResult:
    intent: Intent
    action: Action
    confidence: float
    reasoning: str
