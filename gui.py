import tkinter as tk
from tkinter import ttk, scrolledtext
import asyncio
import threading
import os
import pyaudio
import dotenv

# Internal project imports
from audio_capture.capture import AudioCapture
from stt.vosk_stt import VoskSTT

dotenv.load_dotenv()

class InterviewCopilotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Interview Copilot")
        self.root.geometry("1000x800")
        self.root.configure(bg="#f5f5f5")

        # Session state
        self.loop = None
        self.async_stop_event = None
        self.processing_thread = None
        self.partial_map = {"Me": "", "Interviewer": ""}

        self.setup_ui()
        self.load_devices()

    def setup_ui(self):
        # 1. Device Selection Frame
        top_frame = ttk.LabelFrame(self.root, text="Settings")
        top_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(top_frame, text="Microphone:").grid(row=0, column=0, padx=5, pady=5)
        self.mic_combo = ttk.Combobox(top_frame, width=50, state="readonly")
        self.mic_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(top_frame, text="System Audio:").grid(row=1, column=0, padx=5, pady=5)
        self.sys_combo = ttk.Combobox(top_frame, width=50, state="readonly")
        self.sys_combo.grid(row=1, column=1, padx=5, pady=5)

        self.start_btn = ttk.Button(top_frame, text="Start Session", command=self.toggle_session)
        self.start_btn.grid(row=0, column=2, rowspan=2, padx=20, pady=5)

        # 2. Main Display Area (Transcript + Live)
        display_frame = ttk.LabelFrame(self.root, text="Conversation")
        display_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.transcript_area = scrolledtext.ScrolledText(display_frame, wrap=tk.WORD, height=15, font=("Segoe UI", 10))
        self.transcript_area.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Style tags
        self.transcript_area.tag_configure("Me", foreground="#1a73e8", font=("Segoe UI", 10, "bold"))
        self.transcript_area.tag_configure("Interviewer", foreground="#d93025", font=("Segoe UI", 10, "bold"))
        self.transcript_area.tag_configure("Partial", foreground="gray", font=("Segoe UI", 10, "italic"))

        # 3. Live Stream Indicator
        self.live_label_interviewer = ttk.Label(display_frame, text="Live [Interviewer]: ...", foreground="gray")
        self.live_label_me = ttk.Label(display_frame, text="Live [Me]: ...", foreground="gray")
        self.live_label_interviewer.pack(fill="x", padx=5, pady=2)
        self.live_label_me.pack(fill="x", padx=5, pady=2)

        # 4. AI Answer Area
        answer_frame = ttk.LabelFrame(self.root, text="AI Suggestions")
        answer_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.answer_area = scrolledtext.ScrolledText(answer_frame, wrap=tk.WORD, height=8, font=("Segoe UI", 11), bg="#fffbe6")
        self.answer_area.pack(fill="both", expand=True, padx=5, pady=5)

    def load_devices(self):
        p = pyaudio.PyAudio()
        devices = []
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if int(info["maxInputChannels"]) > 0:
                devices.append(f"{i}: {info['name']}")
        self.mic_combo['values'] = devices
        self.sys_combo['values'] = devices
        p.terminate()

    # --- Callbacks ---

    def on_partial_received(self, speaker, text):
        """Updates the live label at the bottom."""
        self.root.after(0, self._update_live_ui, speaker, text)

    def on_final_received(self, speaker, text):
        """Appends finalized text to the main box."""
        self.root.after(0, self._append_final_ui, speaker, text)

    def on_answer_received(self, text):
        """Displays the LLM suggestion."""
        self.root.after(0, self._display_answer_ui, text)

    # --- Thread-Safe UI Methods ---

    def _update_live_ui(self, speaker, text):
        self.partial_map[speaker] = text
        me_text = self.partial_map["Me"]
        int_text = self.partial_map["Interviewer"]
        status = ""
        if me_text: status += f"[Me]: {me_text} "
        if int_text: status += f"[Interviewer]: {int_text}"
        self.live_label_me.config(text=f"Live [Me]: {me_text}")
        self.live_label_interviewer.config(text=f"Live [Interviewer]: {int_text}")

    def _append_final_ui(self, speaker, text):
        self.partial_map[speaker] = ""  # Reset partial for this speaker
        self.transcript_area.insert(tk.END, f"{speaker}: ", speaker)
        self.transcript_area.insert(tk.END, f"{text}\n")
        self.transcript_area.see(tk.END)
        self._update_live_ui("", "") # Refresh live label

    def _display_answer_ui(self, text):
        self.answer_area.delete(1.0, tk.END)
        self.answer_area.insert(tk.END, text)

    # --- Logic ---

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
        self.processing_thread = threading.Thread(target=self.run_async_loop, args=(mic_idx, sys_idx), daemon=True)
        self.processing_thread.start()

    def stop_session(self):
        if self.loop and self.async_stop_event:
            self.loop.call_soon_threadsafe(self.async_stop_event.set)
        self.start_btn.config(text="Start Session")

    def run_async_loop(self, mic_idx, sys_idx):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.async_stop_event = asyncio.Event()
        self.loop.run_until_complete(self.run_engine(mic_idx, sys_idx))

    async def run_engine(self, mic_idx, sys_idx):
        model_path = "models/vosk-model-en-in-0.5"
        api_key = os.getenv("groq_api_key") or ""
        
        mic_cap = AudioCapture(mic_idx)
        sys_cap = AudioCapture(sys_idx)
        await mic_cap.start()
        await sys_cap.start()

        vosk = VoskSTT(
            model_path, 
            api_key=api_key,
            on_transcript=self.on_final_received,
            on_partial=self.on_partial_received,
            on_answer=self.on_answer_received
        )

        # In your main.py logic, sys_q was sent to Vosk("Me") 
        # and mic_q was sent to Vosk("Interviewer")
        mic_task = asyncio.create_task(vosk.run("Me", mic_cap.get_queue()))
        sys_task = asyncio.create_task(vosk.run("Interviewer", sys_cap.get_queue()))

        if self.async_stop_event:
            await self.async_stop_event.wait()
        
        mic_task.cancel()
        sys_task.cancel()
        await mic_cap.stop()
        await sys_cap.stop()

if __name__ == "__main__":
    root = tk.Tk()
    app = InterviewCopilotGUI(root)
    root.mainloop()