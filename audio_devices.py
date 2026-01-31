import pyaudio

def print_audio_devices():
    p = pyaudio.PyAudio()

    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        print(
            f"{i}: {info['name']} | "
            f"Inputs={info['maxInputChannels']} | "
            f"HostAPI={info['hostApi']} | "
            f"Default sample rate={int(info['defaultSampleRate'])} | "
            f"Outputs={info['maxOutputChannels']}"
        )

    p.terminate()

if __name__ == "__main__":
    print_audio_devices()