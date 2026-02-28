import asyncio
import json
from vosk import Model, KaldiRecognizer

from stt.audio_utils import stereo_to_mono_16k
from nlp.classifier_old import NLPClassifier
from answers.llm_answer_generation_old import LLMAnswerGenerator



class VoskSTT:
    def __init__(self, model_path: str, api_key: str = ""):
        self.model = Model(model_path)
        self.classifier = NLPClassifier()
        self.llm_generator = LLMAnswerGenerator(api_key=api_key)
        
    async def run(self, name: str, audio_queue: asyncio.Queue[bytes], input_rate: int = 44100):
        recognizer = KaldiRecognizer(self.model, 16000)
        recognizer.SetWords(True)

        print(f"[{name}] Vosk STT started")

        while True:
            try:
                pcm = await audio_queue.get()

                pcm_16k = stereo_to_mono_16k(pcm, input_rate=input_rate)

                 # Vosk recognition
                accepted = recognizer.AcceptWaveform(pcm_16k)

                if accepted:
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").strip()
                    if not text:
                        continue
                        

                    print(f"[{name}] FINAL: {text}")
                    if name == "Interviewer":
                        result = await self.classifier.classify(text)
                        print(f"[{name}] Classification result: {result}, action: {result.action}")
                        if result.action == "respond":
                            print(f"[{name}] QUESTION DETECTED: {text} (intent: {result.intent})")
                            llm_answer = await self.llm_generator.generate(
                                question=text,
                                intent=result.intent,
                                mode="concise",
                            )
                            print("[LLM ANSWER]")
                            print(llm_answer.text)

            except asyncio.CancelledError:
                print(f"[{name}] Vosk STT stopped")
                break
