import asyncio
import json
from vosk import Model, KaldiRecognizer

from stt.audio_utils import stereo_to_mono_16k
from nlp.classifier_old import NLPClassifier
from answers.llm_answer_generation_old import LLMAnswerGenerator

class VoskSTT:
    def __init__(self, model_path: str, api_key: str = "", on_transcript=None, on_partial=None, on_answer=None):
        self.model = Model(model_path)
        self.classifier = NLPClassifier()
        self.llm_generator = LLMAnswerGenerator(api_key=api_key, on_answer=on_answer)
        
        # Callbacks for GUI integration
        self.on_transcript = on_transcript  # Finalized text
        self.on_partial = on_partial        # Live "streaming" text
        self.on_answer = on_answer          # AI generated answer
        
    async def run(self, name: str, audio_queue: asyncio.Queue[bytes], input_rate: int = 44100):
        recognizer = KaldiRecognizer(self.model, 16000)
        recognizer.SetWords(True)

        print(f"[{name}] Vosk STT started")
        if self.on_partial:
            self.on_partial(name, "Recognizer initialized, waiting for audio...")

        while True:
            try:
                pcm = await audio_queue.get()
                pcm_16k = stereo_to_mono_16k(pcm, input_rate=input_rate)

                # recognizer.AcceptWaveform returns True when a silence/finality is detected
                if recognizer.AcceptWaveform(pcm_16k):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").strip()
                    
                    if text:
                        if self.on_transcript:
                            self.on_transcript(name, text)
                        print(f"[{name}] FINAL: {text}")

                        if name == "Interviewer":
                            res = await self.classifier.classify(text)
                            if res.action == "respond":
                                llm_answer = await self.llm_generator.generate(
                                    question=text,
                                    intent=res.intent,
                                    mode="concise",
                                )
                                if self.on_answer:
                                    self.on_answer(llm_answer.text)
                else:
                    # This provides the live "stream" of text while speaking
                    partial = json.loads(recognizer.PartialResult())
                    partial_text = partial.get("partial", "").strip()
                    if partial_text and self.on_partial:
                        self.on_partial(name, partial_text)

            except asyncio.CancelledError:
                print(f"[{name}] Vosk STT stopped")
                break