import os
from groq import AsyncGroq
from answers.llm_types import LLMAnswer, LLMMode


class LLMAnswerGenerator:
    def __init__(self, api_key: str | None = None):
        self.client = AsyncGroq(
            api_key=api_key or os.getenv("GROQ_API_KEY")
        )

    async def generate(
        self,
        question: str,
        intent: str,
        mode: str = "concise",
    ) -> LLMAnswer:

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


        try:
            response = await self.client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=180 if mode == "concise" else 350,
            )

            content = response.choices[0].message.content
            text = content.strip() if content is not None else ""

            return LLMAnswer(
                text=text,
                mode=mode,  # type: ignore
                confidence=0.9,
            )

        except Exception as e:
            return self._fallback_answer(intent, str(e))

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
