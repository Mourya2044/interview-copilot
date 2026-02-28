import asyncio
import json
from vosk import Model, KaldiRecognizer
from stt.audio_utils import stereo_to_mono_16k
from nlp.classifier_old import NLPClassifier
from answers.llm_answer_generation_old import LLMAnswerGenerator

class VoskSTT:
    def __init__(self, model_path: str, api_key: str = "", 
                 on_transcript=None, on_answer=None): # Added callbacks
        self.model = Model(model_path)
        self.classifier = NLPClassifier()
        self.llm_generator = LLMAnswerGenerator(api_key=api_key)
        self.on_transcript = on_transcript
        self.on_answer = on_answer
        
    async def run(self, name: str, audio_queue: asyncio.Queue[bytes], input_rate: int = 44100):
        recognizer = KaldiRecognizer(self.model, 16000)
        recognizer.SetWords(True)

        while True:
            try:
                pcm = await audio_queue.get()
                pcm_16k = stereo_to_mono_16k(pcm, input_rate=input_rate)
                accepted = recognizer.AcceptWaveform(pcm_16k)

                if accepted:
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").strip()
                    if not text: continue
                        
                    # Send transcript to GUI if callback exists
                    if self.on_transcript:
                        self.on_transcript(name, text)
                    print(f"[{name}] FINAL: {text}")

                    if name == "Interviewer":
                        classification = await self.classifier.classify(text)
                        if classification.action == "respond":
                            llm_answer = await self.llm_generator.generate(
                                question=text,
                                intent=classification.intent,
                                mode="concise",
                            )
                            # Send answer to GUI if callback exists
                            if self.on_answer:
                                self.on_answer(llm_answer.text)
                            print(f"[LLM ANSWER] {llm_answer.text}")

            except asyncio.CancelledError:
                break