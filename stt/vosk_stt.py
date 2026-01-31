import asyncio
import json
from time import time
from vosk import Model, KaldiRecognizer
import random

from nlp.question_event import QuestionEvent
from nlp.confidence import confidence_score
from stt.audio_utils import debug_amplitude, stereo_44k_to_mono_16k
# from stt.silero_vad import SileroVAD
from nlp.classifier import NLPClassifier
from answers.llm_answer_generation import LLMAnswerGenerator



class VoskSTT:
    def __init__(self, model_path: str, api_key):
        self.model = Model(model_path)
        # self.vad = SileroVAD()
        self.classifier = NLPClassifier()
        self.llm_generator = LLMAnswerGenerator(api_key=api_key)
        
    async def run(self, name: str, audio_queue: asyncio.Queue[bytes]):
        recognizer = KaldiRecognizer(self.model, 16000)
        recognizer.SetWords(True)

        print(f"[{name}] Vosk STT started")

        while True:
            try:
                pcm = await audio_queue.get()

                pcm_16k = stereo_44k_to_mono_16k(pcm)
                # debug_amplitude(pcm_16k, name)

                # VAD: skip silence
                # if not self.vad.is_speech(pcm_16k):
                    # print(f"[{name}] SILENCE")
                    # continue

                # print(f"[{name}] PROCESSING FRAME")

                 # Vosk recognition
                accepted = recognizer.AcceptWaveform(pcm_16k)

                if accepted:
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").strip()
                    if not text:
                        continue
                        

                    print(f"[{name}] FINAL: {text}")
                    if name == "Interviewer":
                        confidence = confidence_score(text)

                        if confidence >= 0.5:
                            text += "?"
                            event = QuestionEvent(speaker=name, text=text, timestamp=time(), confidence=confidence)
                            result = await self.classifier.classify(event)
                            # print(
                            #     f"[CLASSIFIER] intent={result.intent} "
                            #     f"action={result.action} "
                            #     f"confidence={result.confidence:.2f} "
                            #     f"reason={result.reasoning}"
                            # )
                            if result.action == "respond":
                                print(f"[{name}] QUESTION DETECTED: {event.text} (intent: {result.intent})")
                                # optional LLM expansion
                                llm_answer = await self.llm_generator.generate(
                                    question=event.text,
                                    intent=result.intent,
                                    mode="concise",
                                )

                                print("[LLM ANSWER]")
                                print(llm_answer.text)
                                
                elif random.random() < 0.01:  # throttle partials to reduce log spam
                    partial = json.loads(recognizer.PartialResult())
                    text = partial.get("partial", "").strip()
                    if text:
                        print(f"[{name}] PARTIAL: {text}")

            except asyncio.CancelledError:
                print(f"[{name}] Vosk STT stopped")
                break
