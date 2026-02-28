import pyaudio
import threading
import queue
import asyncio

FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
CHUNK = 1024


class AudioCapture:
    def __init__(self, device_index: int, rate: int = RATE, channels: int = CHANNELS):
        self.device_index = device_index
        self.rate = rate
        self.channels = channels

        self._p: pyaudio.PyAudio | None = None
        self._stream = None

        self._sync_queue: queue.Queue[bytes] = queue.Queue(maxsize=200)
        self.async_queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=20)

        self._stop_event = threading.Event()

    # -------- PyAudio callback --------
    def _callback(self, in_data, frame_count, time_info, status):
        # print("CALLBACK", len(in_data))  # TEMP DEBUG
        try:
            self._sync_queue.put_nowait(in_data)
        except queue.Full:
            pass
        return (None, pyaudio.paContinue)

    # -------- Thread bridge --------
    def _bridge(self, loop: asyncio.AbstractEventLoop):
        def _safe_async_put(q: asyncio.Queue, data: bytes):
            try:
                q.put_nowait(data)
            except asyncio.QueueFull:
                pass  # drop frame

        while not self._stop_event.is_set():
            # print("BRIDGE GOT FRAME")  # TEMP DEBUG
            try:
                data = self._sync_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            loop.call_soon_threadsafe(
                _safe_async_put,
                self.async_queue,
                data
            )


    # -------- Lifecycle --------
    async def start(self):
        loop = asyncio.get_running_loop()

        threading.Thread(
            target=self._bridge,
            args=(loop,),
            daemon=True
        ).start()

        self._p = pyaudio.PyAudio()
        self._stream = self._p.open(
            format=FORMAT,
            channels=self.channels,
            rate=self.rate,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=CHUNK,
            stream_callback=self._callback,
        )

        self._stream.start_stream()

    async def stop(self):
        self._stop_event.set()

        if self._stream:
            self._stream.stop_stream()
            self._stream.close()

        if self._p:
            self._p.terminate()

    def get_queue(self) -> asyncio.Queue[bytes]:
        return self.async_queue
