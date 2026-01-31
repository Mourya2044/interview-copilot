import torch
import numpy as np
from silero_vad import load_silero_vad, get_speech_timestamps


class SileroVAD:
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.model = load_silero_vad()

    def is_speech(self, pcm_16k: bytes) -> bool:
        """
        Returns True if speech is detected in this chunk
        """
        # int16 → float32 [-1, 1]
        audio = np.frombuffer(pcm_16k, dtype=np.int16).astype(np.float32)
        audio /= 32768.0

        # Convert to torch tensor
        tensor = torch.from_numpy(audio)

        # Silero expects 1D tensor
        speech_timestamps = get_speech_timestamps(
            tensor,
            self.model,
            sampling_rate=self.sample_rate,
            return_seconds=False,
        )

        return len(speech_timestamps) > 0
