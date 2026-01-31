from nlp.question_event import QuestionEvent
from nlp.question_event import QuestionEvent
from nlp.confidence import confidence_score
import time
from nlp.classifier import NLPClassifier
from answers.llm_answer_generation import LLMAnswerGenerator
from openai import OpenAI
import os
import dotenv

dotenv.load_dotenv()
api_key = os.getenv("groq_api_key")


classifier = NLPClassifier()
llm_generator = LLMAnswerGenerator(api_key=api_key)  # TODO: pass actual client

async def test():
    text = "Can you walk me through a challenging problem you worked on and how you handled it?"
    confidence = confidence_score(text)
    event = QuestionEvent(
        speaker="Interviewer",
        text=text,
        timestamp=time.time(),
        confidence=confidence,
    )
    print(event)
    result = await classifier.classify(event)
    print(result)
    if result.action == "respond":
        print(f"[INTERVIEWER] QUESTION DETECTED: {event.text} (intent: {result.intent})")
        # optional LLM expansion
        llm_answer = await llm_generator.generate(
            question=event.text,
            intent=result.intent,
            mode="concise",
        )

        print("[LLM ANSWER]")
        print(llm_answer.text)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test())