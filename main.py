import asyncio
import dotenv

from audio_devices import print_audio_devices
from stt.realtimeSTT import realtimeSTT
from nlp.classifier import NLPClassifier
from answers.llm_answer_generation import LLMAnswerGenerator

dotenv.load_dotenv()

DEVICE_INDEX = 1
classifier = NLPClassifier()
llm_generator = LLMAnswerGenerator()

async def final_transcription(text):
    # print(f"[Final Transcription]: {text}")
    res = await classifier.classify(text)
    print(f"[Classification Result]: {res}")
    if res.action == "respond":
        llm_answer = await llm_generator.generate(
            question=text,
            intent=res.intent,
            mode="concise",
        )
        print(f"[LLM]: {llm_answer.text}")

def partial_transcription(text):
    print(f"\r[Interviewer] partial: {text}", end="", flush=True)

async def main():    
    interviewer_stt = realtimeSTT(
        name="Interviewer",
        language="en",
        input_device_index=DEVICE_INDEX,
        partial_update=partial_transcription,
        final_update=final_transcription,
    )
    
    try:
        print("\n--- System Active (Press Ctrl+C to stop) ---")
        await interviewer_stt.start()
        
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        print("\n[System] Shutdown signal received...")
    finally:
        print("[System] Cleaning up resources...")
        print("[System] Safe to exit. Goodbye!")

if __name__ == "__main__":
    print_audio_devices()
    try:
        user_input = input("Enter your microphone device index (default 1): ")
        DEVICE_INDEX = int(user_input) if user_input.strip() else 1
        
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[System] Interrupted during setup.")
