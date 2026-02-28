import dotenv
from groq import AsyncGroq
from dataclasses import dataclass
from typing import Literal

dotenv.load_dotenv()

LLMMode = Literal["concise", "detailed"]

@dataclass
class LLMAnswer:
    text: str
    mode: LLMMode
    confidence: float
    
class AnswerGenerator:
    MAX_HISTORY = 10  # limit history to prevent token explosion

    def __init__(self, on_answer=None):
        self.client = AsyncGroq()
        self.history: list[dict] = []
        self.on_answer = on_answer
    async def generate(
        self,
        question: str,
        intent: str,
        mode: str = "concise",
    ) -> LLMAnswer:

        # ----- YOUR ORIGINAL PROMPT (UNCHANGED) -----
        prompt = f"""
You are helping a candidate answer an interview question verbally.

Question:
{question}

Intent:
{intent}

Instructions:
- Answer as if speaking in an interview
- Use plain text only (no markdown, no bullets)
- Limit to 2-3 sentences
- Be clear and confident
- Do NOT mention AI
- Do NOT list options unless explicitly asked

Answer:
""".strip()
        # -------------------------------------------

        # Add the new user prompt into history
        self.history.append({
            "role": "user",
            "content": prompt
        })

        # Trim history (rolling buffer)
        if len(self.history) > self.MAX_HISTORY:
            self.history = self.history[-self.MAX_HISTORY:]

        try:
            response = await self.client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=self.history, # type: ignore
                temperature=0.3,
                stream=True,
            )

            text = ""
            async for chunk in response:
                # You could stream partial content here if desired
                text += chunk.choices[0].delta.content if chunk.choices[0].delta.content else ""
                if self.on_answer:
                    self.on_answer(text)  # Update UI with streaming text
                
            text = text.strip()

            # Store assistant reply for future follow-ups
            self.history.append({
                "role": "assistant",
                "content": text
            })

            # Trim again after assistant reply
            if len(self.history) > self.MAX_HISTORY:
                self.history = self.history[-self.MAX_HISTORY:]

            return LLMAnswer(
                text=text,
                mode=mode,  # type: ignore
                confidence=0.9,
            )

        except Exception as e:
            return self._fallback_answer(intent, str(e))

    def reset_context(self):
        """Call when starting a new interview session."""
        self.history = []

    def _fallback_answer(self, intent: str, reason: str) -> LLMAnswer:
        if intent == "algorithmic":
            text = (
                "Start by restating the problem. "
                "Clarify constraints and edge cases. "
                "Explain the core approach, then analyze time and space complexity."
            )
        elif intent == "behavioral":
            text = (
                "Use the STAR method: describe the situation, "
                "your role, the actions you took, and the result."
            )
        else:
            text = "Ask a clarifying question or explain your thinking briefly."

        return LLMAnswer(
            text=f"[Groq unavailable: {reason}] {text}",
            mode="concise",
            confidence=0.4,
        )