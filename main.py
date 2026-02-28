import asyncio

import pyaudio
from audio_capture.capture import AudioCapture
from audio_devices import print_audio_devices
from stt.vosk_stt import VoskSTT
from openai import OpenAI
import os
import dotenv

dotenv.load_dotenv()
api_key: str = os.getenv("groq_api_key") or ""

MODEL_PATH = "models/vosk-model-en-in-0.5"
    # models\vosk-model-en-in-0.5

# ===== YOU (CMF Buds mic) =====
MIC_DEVICE_INDEX = 1
MIC_RATE = 44100
MIC_CHANNELS = 2

# ===== INTERVIEWER (System audio via Realtek) =====
SYS_DEVICE_INDEX = 2
SYS_RATE = 44100
SYS_CHANNELS = 2


async def main():
    mic_capture = AudioCapture(MIC_DEVICE_INDEX, rate=MIC_RATE, channels=MIC_CHANNELS)
    sys_capture = AudioCapture(SYS_DEVICE_INDEX, rate=SYS_RATE, channels=SYS_CHANNELS)

    await mic_capture.start()
    await sys_capture.start()

    mic_q = mic_capture.get_queue()
    sys_q = sys_capture.get_queue()

    vosk = VoskSTT(MODEL_PATH, api_key=api_key)

    mic_task = asyncio.create_task(vosk.run("Me", sys_q, input_rate=SYS_RATE))
    sys_task = asyncio.create_task(vosk.run("Interviewer", mic_q, input_rate=MIC_RATE))

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
    print_audio_devices()
    p = pyaudio.PyAudio()
    MIC_DEVICE_INDEX = int(input("Enter your microphone device index: "))
    info = p.get_device_info_by_index(MIC_DEVICE_INDEX)
    print(f"Selected microphone device: {info['name']}")
    MIC_RATE = int(info['defaultSampleRate'])
    MIC_CHANNELS = int(info['maxInputChannels'])
    
    
    SYS_DEVICE_INDEX = int(input("Enter your system audio device index: "))
    info = p.get_device_info_by_index(SYS_DEVICE_INDEX)
    print(f"Selected system audio device: {info['name']}")
    SYS_RATE = int(info['defaultSampleRate'])
    SYS_CHANNELS = int(info['maxInputChannels'])
    p.terminate()
    
    
    asyncio.run(main())
