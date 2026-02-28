from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from nlp.classifier_types import ClassificationResult

load_dotenv()


class NLPClassifier:
    """
    Context-aware interview classifier.
    Keeps rolling conversation memory for follow-up detection.
    """

    MAX_HISTORY = 4  # keep last few messages only

    def __init__(self, api_key: str | None = None):
        self.model = (
            init_chat_model(
                "gpt-4.1-mini",
                temperature=0,
            )
            .with_structured_output(ClassificationResult)
        )

        self.history = []

    async def classify(self, text: str) -> ClassificationResult:
        print(f"[CLASSIFIER] Classifying: {text}")
        text = text.strip()

        if not text:
            return ClassificationResult(
                intent="none",
                action="ignore",
                confidence=1.0,
                reasoning="Empty text",
            )

        # Basic cheap pre-filter
        lower = text.lower()
        if lower in {"okay", "ok", "thanks", "thank you", "great", "nice"}:
            return ClassificationResult(
                intent="none",
                action="ignore",
                confidence=0.95,
                reasoning="Acknowledgement",
            )

        # print(f"[CLASSIFIER] History length: {len(self.history)}")
        # Add current message to rolling context
        self.history.append({"role": "user", "content": text})
        if len(self.history) > self.MAX_HISTORY:
            self.history = self.history[-self.MAX_HISTORY:]

        system_prompt = """
You classify interview speech transcripts.

Only classify the MOST RECENT message.
Do not infer intent from older messages unless the latest message is meaningful.

Return structured output only and keep it extremely concise.

Types:
- question
- follow_up
- not_a_question

Rules:

1. If the latest message is:
   - Filler (yeah, hmm, okay)
   - Single word (unless clearly a question like "Why?")
   - Grammatically invalid
   - Incomplete or nonsensical
   → classify as not_a_question
   → intent = none
   → action = ignore

2. question:
   - Clear, complete standalone interview question.

3. follow_up:
   - Latest message must be a meaningful complete sentence
   - AND continue the previous topic.

4. If the latest message is unclear or broken,
   ignore previous context and return not_a_question.

Be conservative.
When unsure, choose not_a_question.
"""

        messages = [{"role": "system", "content": system_prompt}] + self.history

        try:
            # print(f"[CLASSIFIER] Sending to model with {len(messages)} messages")
            result = self.model.invoke(messages) # type: ignore
            # print(f"[CLASSIFIER] Model result: {result}")
            return ClassificationResult(
                intent=result['intent'], # type: ignore
                action=result['action'], # type: ignore
                confidence=result['confidence'], # type: ignore
                reasoning=result['reasoning'], # type: ignore
            )

        except Exception as e:
            print(f"[CLASSIFIER] Error during classification: {str(e)}")
            return ClassificationResult(
                intent="unknown",
                action="ignore",
                confidence=0.0,
                reasoning=f"Classification error: {str(e)}",
            )

    def reset_context(self):
        self.history = []