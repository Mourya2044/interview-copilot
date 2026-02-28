import pyaudio


def print_audio_devices():
    p = pyaudio.PyAudio()

    input_devices = []
    output_devices = []

    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)

        device_info = {
            "index": i,
            "name": info["name"],
            "hostApi": info["hostApi"],
            "rate": int(info["defaultSampleRate"]),
            "inputs": info["maxInputChannels"],
            "outputs": info["maxOutputChannels"],
        }

        if int(info["maxInputChannels"]) > 0:
            input_devices.append(device_info)

        if int(info["maxOutputChannels"]) > 0:
            output_devices.append(device_info)

    print("\n🎤 INPUT DEVICES (Microphones / Stereo Mix)\n")
    for d in input_devices:
        print(
            f"{d['index']}: {d['name']} | "
            f"Inputs={d['inputs']} | "
            f"Outputs={d['outputs']} | "
            f"Rate={d['rate']} | "
            f"HostAPI={d['hostApi']}"
        )

    print("\n🔊 OUTPUT DEVICES (Speakers / Headphones)\n")
    for d in output_devices:
        print(
            f"{d['index']}: {d['name']} | "
            f"Inputs={d['inputs']} | "
            f"Outputs={d['outputs']} | "
            f"Rate={d['rate']} | "
            f"HostAPI={d['hostApi']}"
        )

    p.terminate()


if __name__ == "__main__":
    print_audio_devices()
