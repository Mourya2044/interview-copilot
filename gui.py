import tkinter as tk
from tkinter import ttk, scrolledtext
import asyncio
import threading
import os
import pyaudio
import dotenv

# Internal imports from your project
from audio_capture.capture import AudioCapture
from stt.vosk_stt import VoskSTT

dotenv.load_dotenv()

class InterviewCopilotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Interview Copilot")
        self.root.geometry("900x700")
        
        self.loop = None
        self.stop_event = None
        self.processing_thread = None
        
        self.setup_ui()
        self.load_devices()

    def setup_ui(self):
        # Configuration Panel
        config_frame = ttk.LabelFrame(self.root, text="Audio Configuration")
        config_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(config_frame, text="My Microphone:").grid(row=0, column=0, padx=5, pady=5)
        self.mic_combo = ttk.Combobox(config_frame, width=60, state="readonly")
        self.mic_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(config_frame, text="System Audio:").grid(row=1, column=0, padx=5, pady=5)
        self.sys_combo = ttk.Combobox(config_frame, width=60, state="readonly")
        self.sys_combo.grid(row=1, column=1, padx=5, pady=5)

        self.start_btn = ttk.Button(config_frame, text="Start Session", command=self.toggle_session)
        self.start_btn.grid(row=0, column=2, rowspan=2, padx=20, pady=5)

        # Transcript Panel
        trans_frame = ttk.LabelFrame(self.root, text="Live Conversation")
        trans_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.transcript_box = scrolledtext.ScrolledText(trans_frame, wrap=tk.WORD, height=15, font=("Segoe UI", 10))
        self.transcript_box.pack(fill="both", expand=True, padx=5, pady=5)
        self.transcript_box.tag_configure("Me", foreground="blue")
        self.transcript_box.tag_configure("Interviewer", foreground="red", font=("Segoe UI", 10, "bold"))

        # Answer Panel
        ans_frame = ttk.LabelFrame(self.root, text="Suggested Response")
        ans_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.answer_box = scrolledtext.ScrolledText(ans_frame, wrap=tk.WORD, height=8, font=("Segoe UI", 11), bg="#f9f9f9")
        self.answer_box.pack(fill="both", expand=True, padx=5, pady=5)

    def load_devices(self):
        p = pyaudio.PyAudio()
        input_devices = []
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if int(info["maxInputChannels"]) > 0:
                input_devices.append(f"{i}: {info['name']}")
        
        self.mic_combo['values'] = input_devices
        self.sys_combo['values'] = input_devices
        p.terminate()

    def update_transcript(self, speaker, text):
        """Thread-safe update for the transcript box."""
        self.root.after(0, self._safe_append_transcript, speaker, text)

    def _safe_append_transcript(self, speaker, text):
        self.transcript_box.insert(tk.END, f"{speaker}: ", speaker)
        self.transcript_box.insert(tk.END, f"{text}\n")
        self.transcript_box.see(tk.END)

    def update_answer(self, text):
        """Thread-safe update for the answer box."""
        self.root.after(0, self._safe_set_answer, text)

    def _safe_set_answer(self, text):
        self.answer_box.delete(1.0, tk.END)
        self.answer_box.insert(tk.END, text)

    def toggle_session(self):
        if self.processing_thread and self.processing_thread.is_alive():
            self.stop_session()
        else:
            self.start_session()

    def start_session(self):
        if not self.mic_combo.get() or not self.sys_combo.get():
            return
            
        mic_idx = int(self.mic_combo.get().split(":")[0])
        sys_idx = int(self.sys_combo.get().split(":")[0])
        
        self.start_btn.config(text="Stop Session")
        self.stop_event = threading.Event()
        self.processing_thread = threading.Thread(
            target=self.run_async_wrapper, 
            args=(mic_idx, sys_idx), 
            daemon=True
        )
        self.processing_thread.start()

    def stop_session(self):
        if self.loop:
            self.loop.call_soon_threadsafe(self.async_stop_event.set)
        self.start_btn.config(text="Start Session")

    def run_async_wrapper(self, mic_idx, sys_idx):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.async_stop_event = asyncio.Event()
        self.loop.run_until_complete(self.run_engine(mic_idx, sys_idx))

    async def run_engine(self, mic_idx, sys_idx):
        model_path = "models/vosk-model-en-in-0.5"
        api_key = os.getenv("groq_api_key") or ""
        
        # Initialize components
        mic_cap = AudioCapture(mic_idx)
        sys_cap = AudioCapture(sys_idx)
        await mic_cap.start()
        await sys_cap.start()
        
        vosk = VoskSTT(
            model_path, 
            api_key=api_key, 
            on_transcript=self.update_transcript,
            on_answer=self.update_answer
        )
        
        mic_task = asyncio.create_task(vosk.run("Me", sys_cap.get_queue()))
        sys_task = asyncio.create_task(vosk.run("Interviewer", mic_cap.get_queue()))
        
        # Wait until stop signal
        await self.async_stop_event.wait()
        
        mic_task.cancel()
        sys_task.cancel()
        await mic_cap.stop()
        await sys_cap.stop()

if __name__ == "__main__":
    root = tk.Tk()
    app = InterviewCopilotGUI(root)
    root.mainloop()