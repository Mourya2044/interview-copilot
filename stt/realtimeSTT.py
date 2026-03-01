from RealtimeSTT import AudioToTextRecorder

class realtimeSTT:
    def __init__(self, partial_update, final_update, name=None, on_ready=None, on_error=None, language="en", input_device_index=1, console_output=False):
        self.name = name
        self.final_update = final_update
        self.on_ready = on_ready
        self.on_error = on_error
        self.running = True
        self.console_output = console_output
        
        self.recorder = AudioToTextRecorder(
            model="base.en",
            realtime_model_type="tiny.en", 
            language=language,
            enable_realtime_transcription=True,
            input_device_index=input_device_index,
            # on_realtime_transcription_update=partial_update,
            on_realtime_transcription_stabilized=partial_update,
            no_log_file=True,
            compute_type="int8",
            spinner=console_output
        )

    async def start(self):
        if self.on_ready is not None:
            self.on_ready()
        if self.console_output:
            print(f"[{self.name=}] Listening... (Speak now)")
        # self.recorder.start()
        while self.running:
            full_sentence = self.recorder.text()
            await self.final_update(full_sentence)
    
    def stop(self):
        self.running = False
        try:
            self.recorder.shutdown()
        except Exception as e:
            if self.console_output:
                print(f"[{self.name=}] Error stopping recorder: {e}")
            if self.on_error is not None:
                self.on_error(e)