import customtkinter as ctk
import asyncio
import threading
import pyaudio
from stt.realtimeSTT import realtimeSTT
from nlp.classifier import NLPClassifier
from nlp.answer_generation import AnswerGenerator
import ctypes

# Add these constants at the top of your file
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20

def set_click_through(hwnd, enabled=True):
    """
    Enables or disables mouse click-through for the window.
    """
    try:
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        if enabled:
            # Add transparent and layered styles
            style |= (WS_EX_TRANSPARENT | WS_EX_LAYERED)
        else:
            # Remove transparent style
            style &= ~WS_EX_TRANSPARENT
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
    except Exception as e:
        print(f"Error setting click-through: {e}")

def ensure_stealth(window):
    """
    Excludes the window from all screen capture and recording.
    """
    # WDA_EXCLUDEFROMCAPTURE (0x00000011) is supported on Windows 10 version 2004+
    # It makes the window invisible to capture but fully visible to the user.
    try:
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 0x00000011)
    except Exception as e:
        # Fallback to WDA_MONITOR (0x01) for older Windows 10 versions
        ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 0x00000001)

class ModernCopilotGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("Interview Copilot")
        self.geometry("900x650")
        # ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        
        # --- STEALTH COMMANDS ---
        self.attributes("-alpha", 0.70)  # Makes the window semi-transparent
        self.attributes("-topmost", True)  # Keeps the window floating over other apps
        # We use after() to ensure the window is fully rendered before applying protection
        self.after(100, lambda: self.apply_initial_styles) 
        # ------------------------

        # Handle window close button
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar_label = ctk.CTkLabel(self.sidebar, text="System Control", font=ctk.CTkFont(size=20, weight="bold"))
        self.sidebar_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.sidebar.bind("<ButtonPress-1>", self.start_move)
        self.sidebar.bind("<B1-Motion>", self.do_move)
        
        # Audio Device Selector
        self.device_label = ctk.CTkLabel(self.sidebar, text="Select Microphone:")
        self.device_label.grid(row=1, column=0, padx=20, pady=(10, 0))
        
        self.device_map = self.get_audio_devices()
        self.device_dropdown = ctk.CTkOptionMenu(self.sidebar, values=list(self.device_map.keys()))
        self.device_dropdown.set(list(self.device_map.keys())[2])
        self.device_dropdown.grid(row=2, column=0, padx=20, pady=10)

        self.status_label = ctk.CTkLabel(self.sidebar, text="Status: Ready", text_color="gray")
        self.status_label.grid(row=3, column=0, padx=20, pady=10)

        self.start_btn = ctk.CTkButton(self.sidebar, text="Start Session", command=self.start_session)
        self.start_btn.grid(row=4, column=0, padx=20, pady=10)
        
        self.stop_btn = ctk.CTkButton(self.sidebar, text="Stop Session", state="disabled", command=self.stop_session)
        self.stop_btn.grid(row=5, column=0, padx=20, pady=10)

        self.check_mouse_position()
        
        # Allow dragging the window via the sidebar
        self.start_btn.bind("<ButtonPress-1>", self.start_move)
        self.stop_btn.bind("<ButtonPress-1>", self.start_move)
        self.start_btn.bind("<B1-Motion>", self.do_move)
        self.stop_btn.bind("<B1-Motion>", self.do_move)
        
        # Main Content Area
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(4, weight=4)

        # Transcription Display
        self.transcript_label = ctk.CTkLabel(self.main_frame, text="Live Transcription", font=ctk.CTkFont(size=14, weight="bold"))
        self.transcript_label.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="w")
        self.transcript_box = ctk.CTkTextbox(self.main_frame, height=150)
        self.transcript_box.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        # AI Answer Display
        self.answer_label = ctk.CTkLabel(self.main_frame, text="AI Suggested Answer", font=ctk.CTkFont(size=14, weight="bold"))
        self.answer_label.grid(row=2, column=0, padx=20, pady=(10, 0), sticky="w")
        self.answer_box = ctk.CTkTextbox(self.main_frame, height=250, fg_color="#2b2b2b", text_color="#50fa7b")
        self.answer_box.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        
        self.classifier = NLPClassifier()
        self.llm_generator = AnswerGenerator()
        self.stt = None
        self.loop = None
    
    def apply_initial_styles(self):
        hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
        if hwnd == 0: hwnd = self.winfo_id()
        
        ensure_stealth(self)
        # Optional: Start with click-through DISABLED so you can move the window
        # set_click_through(hwnd, enabled=False)

    def check_mouse_position(self):
        """
        Global loop that checks if the mouse is over the sidebar, 
        independent of transparency.
        """
        try:
            # Get mouse position relative to screen
            pointer_x = self.winfo_pointerx()
            pointer_y = self.winfo_pointery()

            # Get sidebar position and dimensions relative to screen
            self.start_btn_x = self.start_btn.winfo_rootx()
            self.start_btn_y = self.start_btn.winfo_rooty()
            self.start_btn_w = self.start_btn.winfo_width()
            self.start_btn_h = self.start_btn.winfo_height()
            self.stop_btn_x = self.stop_btn.winfo_rootx()
            self.stop_btn_y = self.stop_btn.winfo_rooty()
            self.stop_btn_w = self.stop_btn.winfo_width()
            self.stop_btn_h = self.stop_btn.winfo_height()

            # Check if mouse is within sidebar bounds
            in_start_btn = (self.start_btn_x <= pointer_x <= self.start_btn_x + self.start_btn_w and
                          self.start_btn_y <= pointer_y <= self.start_btn_y + self.start_btn_h)
            in_stop_btn = (self.stop_btn_x <= pointer_x <= self.stop_btn_x + self.stop_btn_w and
                          self.stop_btn_y <= pointer_y <= self.stop_btn_y + self.stop_btn_h)
            

            # Update interaction state
            self.toggle_interaction(in_start_btn or in_stop_btn)

        except Exception:
            pass
        
        # Run this check every 100ms
        self.after(100, self.check_mouse_position)

    def toggle_interaction(self, interactive):
        """Forces the window to be solid/interactive based on screen coordinates."""
        hwnd = ctypes.windll.user32.GetParent(self.winfo_id()) or self.winfo_id()
        
        # Use a state flag to avoid flickering the Win32 API constantly
        current_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        is_transparent = current_style & WS_EX_TRANSPARENT

        if interactive and is_transparent:
            # Mouse is over sidebar: DISABLE click-through
            set_click_through(hwnd, enabled=False)
            # self.attributes("-alpha", 1.0)
            self.status_label.configure(text_color="#50fa7b") # Visual feedback
        
        elif not interactive and not is_transparent:
            # Mouse left sidebar: ENABLE click-through (only if session is active)
            if self.stt and self.stt.running:
                set_click_through(hwnd, enabled=True)
                # self.attributes("-alpha", 0.70)
                self.status_label.configure(text_color="gray")

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")
    
    def get_audio_devices(self):
        """Fetches available input devices."""
        p = pyaudio.PyAudio()
        devices = {}
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if int(info.get('maxInputChannels', 0)) > 0:
                devices[f"{i}: {info['name']}"] = i
        p.terminate()
        return devices

    # ... inside ModernCopilotGUI class ...

    async def gui_final_update(self, text):
        # Schedule the UI update on the main thread
        self.after(0, self.update_transcript, f"Question: {text}")
        
        res = await self.classifier.classify(text)
        if res.action == "respond":
            llm_answer = await self.llm_generator.generate(question=text, intent=res.intent)
            # Schedule the AI answer update on the main thread
            self.after(0, self.update_answer, llm_answer.text)

    def gui_partial_update(self, text):
        # Use after() to schedule the update, but ensure the method 
        # it calls is purely for UI manipulation
        self.after(0, self.update_transcript, text)

    def update_transcript(self, text):
        """Thread-safe update for the transcription box."""
        try:
            self.transcript_box.delete("1.0", "end")
            self.transcript_box.insert("1.0", text)
            self.transcript_box.see("end")
        except Exception as e:
            print(f"UI Update Error: {e}")

    def update_answer(self, text):
        """Thread-safe update for the answer box."""
        try:
            self.answer_box.delete("1.0", "end")
            self.answer_box.insert("1.0", text)
            self.answer_box.see("end")
        except Exception as e:
            print(f"UI Update Error: {e}")

    def start_session(self):
        self.status_label.configure(text="Status: Starting...", text_color="#ffa620")
        self.start_btn.configure(state="disabled")
        self.device_dropdown.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        
        device_name = self.device_dropdown.get()
        device_index = self.device_map[device_name]

        # Initialize STT with selected device
        self.stt = realtimeSTT(
            name="Interviewer",
            input_device_index=device_index,
            partial_update=self.gui_partial_update,
            final_update=self.gui_final_update
        )
        
        # Launch logic in background thread
        threading.Thread(target=self.run_logic, daemon=True).start()
        self.status_label.configure(text="Status: Listening...", text_color="#50fa7b")
        hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
        if hwnd == 0: hwnd = self.winfo_id()
        set_click_through(hwnd, enabled=True)
        
        self.title("Interview Copilot - Clickthrough Active")
    
    def on_ready(self):
        self.status_label.configure(text="Status: Listening...", text_color="#50fa7b")

    def stop_session(self):
        if self.stt:
            self.stt.stop()
        self.status_label.configure(text="Status: Stopped", text_color="#ff5555")
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
        if hwnd == 0: hwnd = self.winfo_id()
        set_click_through(hwnd, enabled=False)
        self.title("Interview Copilot")

    def run_logic(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        if self.stt:
            self.loop.run_until_complete(self.stt.start())

    def on_closing(self):
        """Properly closes all resources before exiting."""
        if self.stt:
            self.stt.stop()
        self.destroy()

if __name__ == "__main__":
    try:
        app = ModernCopilotGUI()
        app.mainloop()
    except KeyboardInterrupt:
        app.on_closing()