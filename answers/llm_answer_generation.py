import requests
from dotenv import load_dotenv
from dataclasses import dataclass

from answers.llm_types import LLMAnswer
load_dotenv()

from langchain.chat_models import init_chat_model
# from langchain.messages import SystemMessage, HumanMessage, AIMessage
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver

system_prompt = (
            "You generate spoken interview answers. "
            "Use prior conversation context if relevant. "
            "Be concise, confident, and natural. "
            "No markdown. No bullet points. No meta commentary."
        )

class LLMAnswerGenerator:
    def __init__(self, api_key: str | None = None):
        self.checkpointer = InMemorySaver()
        self.config = {'configurable': {'thread_id': 1}}
        self.model = init_chat_model('gpt-4.1-mini', temperature=0.1)
        self.agent = create_agent(
            model=self.model,
            system_prompt=system_prompt,
            response_format=LLMAnswer,
            checkpointer=self.checkpointer
        )

    async def generate(
        self,
        question: str,
        intent: str,
        mode: str = "concise",
    ) -> LLMAnswer:
        # print(f"[LLM GENERATOR] Generating answer for intent='{intent}' with question: {question}")
        prompt = f"""
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
            response = self.agent.invoke({
                'messages': [
                    {"role": "user", "content": prompt}
                ]},
                config=self.config, # type: ignore
            )

            content = response['structured_response'].text
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
            text=f"[OPENAI unavailable: {reason}] {text}",
            mode="concise",
            confidence=0.4,
        )
