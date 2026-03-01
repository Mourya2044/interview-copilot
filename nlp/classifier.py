import os
import json
import dotenv
from groq import AsyncGroq
from dataclasses import dataclass
from typing import Literal

dotenv.load_dotenv()

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

class NLPClassifier:
    """
    Flexible LLM-based classifier with context memory.
    """

    MAX_HISTORY = 10  # prevent token explosion

    def __init__(self, console_output=False):
        self.client = AsyncGroq()
        self.history: list[dict] = []
        self.console_output = console_output

    async def classify(self, text: str) -> ClassificationResult:
        # print(f"[CLASSIFIER] Classifying: {text}")
        text = text.strip()

        # Fast STT guard
        if not text or len(text.split()) < 2:
            return ClassificationResult(
                intent="filler",
                action="ignore",
                confidence=0.9,
                reasoning="Too short or likely STT fragment",
            )

        system_prompt = """
You classify interview speech transcripts.

Return ONLY valid JSON:
{
  "intent": string,
  "action": "respond | ignore",
  "confidence": number (0.0-1.0),
  "reasoning": string
}

Rules:

1. If the text is filler, incomplete, broken, random, or grammatically invalid:
   action = ignore

2. If the text is a clear interview question:
   action = respond

3. Intent should be a short descriptive label.

4. Be conservative.
   When unsure, prefer action = ignore.

Only classify the latest message.
Use previous messages only if the latest message is meaningful.
Provide extremely concise reasoning.
"""

        # Add latest message to history
        # self.history.append({"role": "user", "content": text})

        # Trim history
        if len(self.history) > self.MAX_HISTORY:
            self.history = self.history[-self.MAX_HISTORY:]

        try:
            messages = [{"role": "system", "content": system_prompt}] + self.history + [{"role": "user", "content": text}]

            response = await self.client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages, # type: ignore
                temperature=0,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            parsed = json.loads(content)  # type: ignore

            if self.console_output:
                print(f"[CLASSIFIER] Parsed result: {parsed}")

            # Store assistant reply to maintain continuity
            if parsed.get("action") == "respond":
                self.history.append({
                    "role": "assistant",
                    "content": content
                })

            if len(self.history) > self.MAX_HISTORY:
                self.history = self.history[-self.MAX_HISTORY:]

            return ClassificationResult(
                intent=parsed.get("intent", "unknown"),
                action=parsed.get("action", "ignore"),
                confidence=float(parsed.get("confidence", 0.5)),
                reasoning=parsed.get("reasoning", ""),
            )

        except Exception as e:
            return ClassificationResult(
                intent="unknown",
                action="ignore",
                confidence=0.0,
                reasoning=f"LLM classification error: {str(e)}",
            )

    def reset_context(self):
        """Call when starting a new interview session."""
        self.history = []