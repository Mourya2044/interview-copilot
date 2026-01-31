class UtteranceAggregator:
    def __init__(self, silence_timeout: float = 1.2) -> None:
        self.silence_timeout = silence_timeout
        self.buffer: list[str] = []
        self.last_ts: float | None = None

    def add(self, text: str, timestamp: float) -> None:
        if self.last_ts is None:
            self.buffer = [text]
        else:
            self.buffer.append(text)

        self.last_ts = timestamp

    def should_emit(self, now: float) -> bool:
        if not self.buffer or self.last_ts is None:
            return False
        return (now - self.last_ts) >= self.silence_timeout

    def emit(self) -> str:
        text = " ".join(self.buffer).strip()
        self.buffer.clear()
        self.last_ts = None
        return text
