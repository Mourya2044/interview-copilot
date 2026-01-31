from dataclasses import dataclass
import time


@dataclass
class QuestionEvent:
    def __init__(self, speaker: str, text: str, timestamp: float, confidence: float):
        self.speaker = speaker
        self.text = text
        self.timestamp = timestamp
        self.confidence = confidence
        
    def __str__(self):
        return f"QuestionEvent(speaker={self.speaker}, text={self.text}, timestamp={self.timestamp}, confidence={self.confidence})"
