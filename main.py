import asyncio
from audio_capture.capture import AudioCapture
from stt.vosk_stt import VoskSTT
from openai import OpenAI
import os
import dotenv

dotenv.load_dotenv()
api_key: str = os.getenv("groq_api_key") or ""

MODEL_PATH = "models/vosk-model-en-in-0.5"
    # models\vosk-model-en-in-0.5

MIC_DEVICE_INDEX = 1
SYS_DEVICE_INDEX = 2


async def main():
    mic_capture = AudioCapture(MIC_DEVICE_INDEX)
    sys_capture = AudioCapture(SYS_DEVICE_INDEX)

    await mic_capture.start()
    await sys_capture.start()

    mic_q = mic_capture.get_queue()
    sys_q = sys_capture.get_queue()

    vosk = VoskSTT(MODEL_PATH, api_key=api_key)

    mic_task = asyncio.create_task(vosk.run("Me", mic_q))
    sys_task = asyncio.create_task(vosk.run("Interviewer", sys_q))

    print("Vosk STT running. Press Ctrl+C to stop.")

    try:
        await asyncio.Future()  # run forever
    except asyncio.CancelledError:
        pass
    finally:
        print("\nShutting down...")

        mic_task.cancel()
        sys_task.cancel()

        await asyncio.gather(mic_task, sys_task, return_exceptions=True)
        await mic_capture.stop()
        await sys_capture.stop()

        print("Shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
