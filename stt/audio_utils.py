import numpy as np

def debug_amplitude(pcm_16k: bytes, name: str):
    audio = np.frombuffer(pcm_16k, dtype=np.int16)
    if audio.size == 0:
        return
    mean_amp = np.abs(audio).mean()
    max_amp = np.abs(audio).max()
    print(f"[{name}] AMP mean={mean_amp:.1f} max={max_amp}")


def stereo_44k_to_mono_16k(pcm_bytes: bytes) -> bytes:
    """
    Convert stereo 44.1kHz PCM → mono 16kHz PCM
    """
    audio = np.frombuffer(pcm_bytes, dtype=np.int16)
    audio = audio.reshape(-1, 2)
    mono = audio.mean(axis=1)

    # naive but fast resample
    resampled = np.interp(
        np.linspace(0, len(mono), int(len(mono) * 16000 / 44100), endpoint=False),
        np.arange(len(mono)),
        mono
    )

    return resampled.astype(np.int16).tobytes()


def is_speech(pcm_16k: bytes, threshold: int = 500) -> bool:
    """
    Simple energy-based VAD
    """
    audio = np.frombuffer(pcm_16k, dtype=np.int16)
    return audio.size > 0 and abs(audio).mean() > threshold
