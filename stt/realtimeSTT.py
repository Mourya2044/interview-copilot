from RealtimeSTT import AudioToTextRecorder

class realtimeSTT:
    def __init__(self, name, language="en", input_device_index=1, partial_update=None, final_update=None):
        self.name = name
        self.final_update = final_update
        self.running = True
        self.recorder = AudioToTextRecorder(
            model="base.en",
            realtime_model_type="tiny.en", 
            language=language,
            enable_realtime_transcription=True,
            input_device_index=input_device_index,
            on_realtime_transcription_update=partial_update,
            no_log_file=True,
            compute_type="int8",
        )

    async def start(self):
        print(f"[{self.name}] Listening... (Speak now)")
        while self.running:
            full_sentence = self.recorder.text()
            if self.final_update is not None:
                await self.final_update(full_sentence)
    
    def stop(self):
        self.running = False
        try:
            self.recorder.stop()
        except Exception as e:
            print(f"[{self.name}] Error stopping recorder: {e}")