import customtkinter as ctk
import asyncio
import threading
import ctypes
from stt.realtimeSTT import realtimeSTT
from nlp.classifier import NLPClassifier
from nlp.answer_generation import AnswerGenerator

# --- Win32 Stealth Constants ---
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20
WDA_EXCLUDEFROMCAPTURE = 0x00000011
WS_EX_TOOLWINDOW = 0x00000080  # The secret to hiding from Taskbar
WS_EX_APPWINDOW = 0x00040000   # The style we want to remove

def set_click_through(hwnd, enabled=True):
    try:
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        if enabled:
            style |= (WS_EX_TRANSPARENT | WS_EX_LAYERED)
        else:
            style &= ~WS_EX_TRANSPARENT
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
    except Exception: pass

def ensure_stealth(window):
    try:
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id()) or window.winfo_id()
        ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
    except Exception: pass

class UltraMinimalHUD(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.geometry("900x80")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.9)
        self.configure(fg_color="#0d0d0d")

        self.accent = "#50fa7b"
        self.active = False

        # --- Layout ---
        self.grid_columnconfigure(1, weight=0) 
        self.grid_columnconfigure(2, weight=1) 
        self.grid_rowconfigure(0, weight=1)

        # 1. DRAG HANDLE
        self.drag_handle = ctk.CTkFrame(self, width=25, corner_radius=0, fg_color="#1a1a1a",)
        self.drag_handle.grid(row=0, column=0, sticky="nsew")
        self.drag_handle.configure(cursor="fleur")
        
        self.handle_label = ctk.CTkLabel(self.drag_handle, text="⋮\n⋮\n⋮", padx=10, 
                                        text_color="#444", font=("Arial", 16))
        self.handle_label.pack(expand=True)

        # 2. TOGGLE BUTTON
        self.btn_toggle = ctk.CTkButton(self, text="▶", width=40, height=40, 
                                       fg_color="transparent", text_color=self.accent, 
                                       hover_color="#222", font=("Arial", 18, "bold"),
                                       command=self.toggle_session)
        self.btn_toggle.grid(row=0, column=1, padx=10, sticky="n", pady=5)

        # 3. DISPLAY AREA
        self.display_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.display_frame.grid(row=0, column=2, sticky="nsew", pady=5)
        self.display_frame.grid_columnconfigure(0, weight=1)

        self.transcript_line = ctk.CTkLabel(self.display_frame, text="System Standby", 
                                          font=("Inter", 13), text_color="#666", anchor="w")
        self.transcript_line.grid(row=0, column=0, sticky="ew")

        self.answer_box = ctk.CTkTextbox(self.display_frame, height=0, fg_color="#141414",
                                       border_width=1, border_color=self.accent,
                                       font=("Consolas", 13), text_color=self.accent, 
                                       wrap="word", corner_radius=4)
        self.answer_box.grid(row=1, column=0, sticky="nsew", pady=(2, 2))

        # 4. CLOSE BUTTON
        self.close_btn = ctk.CTkButton(self, text="×", width=30, height=30,
                                      fg_color="transparent", text_color="#ff5555",
                                      hover_color="#331111", font=("Arial", 20),
                                      command=self.on_closing)
        self.close_btn.grid(row=0, column=3, padx=10, sticky="ne", pady=5)

        # Logic
        self.classifier = NLPClassifier()
        self.llm_generator = AnswerGenerator()
        self.stt = None

        self.drag_handle.bind("<ButtonPress-1>", self.start_move)
        self.drag_handle.bind("<B1-Motion>", self.do_move)
        self.handle_label.bind("<ButtonPress-1>", self.start_move)
        self.handle_label.bind("<B1-Motion>", self.do_move)
        
        self.after(10, self.hide_from_taskbar)
        self.after(100, self.apply_initial_styles)
        self.check_mouse_position()
    
    def hide_from_taskbar(self):
        """Removes the application icon from the Windows Taskbar."""
        try:
            # Get the window handle (HWND)
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if hwnd == 0: hwnd = self.winfo_id()
            
            # Get current extended styles
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            
            # Remove AppWindow style and Add ToolWindow style
            style = style & ~WS_EX_APPWINDOW
            style = style | WS_EX_TOOLWINDOW
            
            # Apply the new style
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
            
            # Force the window to update its taskbar presence
            # By hiding and showing it quickly
            self.withdraw()
            self.after(10, self.deiconify)
        except Exception as e:
            print(f"Taskbar Stealth Error: {e}")

    def check_mouse_position(self):
        try:
            px, py = self.winfo_pointerx(), self.winfo_pointery()
            widgets = [self.drag_handle, self.btn_toggle, self.close_btn]
            over_interactive = False
            for w in widgets:
                wx, wy = w.winfo_rootx(), w.winfo_rooty()
                ww, wh = w.winfo_width(), w.winfo_height()
                if wx <= px <= wx + ww and wy <= py <= wy + wh:
                    over_interactive = True
                    break
            
            ax = self.answer_box.winfo_rootx()
            ay = self.answer_box.winfo_rooty()
            aw = self.answer_box.winfo_width()
            ah = self.answer_box.winfo_height()
            if ax + aw - 100 <= px <= ax + aw and ay <= py <= ay + ah:
                over_interactive = True
            
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id()) or self.winfo_id()
            if over_interactive:
                set_click_through(hwnd, enabled=False)
                self.attributes("-alpha", 1.0)
            elif self.active:
                set_click_through(hwnd, enabled=True)
                self.attributes("-alpha", 0.7)
        except: pass
        self.after(100, self.check_mouse_position)

    def start_move(self, event):
        self.x, self.y = event.x, event.y

    def do_move(self, event):
        self.geometry(f"+{self.winfo_x() + (event.x - self.x)}+{self.winfo_y() + (event.y - self.y)}")

    def apply_initial_styles(self):
        ensure_stealth(self)

    def toggle_session(self):
        if not self.active:
            # Starting Phase
            self.active = True
            self.btn_toggle.configure(text="...", text_color="#ffa620", state="disabled")
            self.transcript_line.configure(text="Initializing...", text_color="#ffa620")
            
            # Use after() to let the UI update before blocking the thread with STT init
            self.after(200, self.launch_stt_thread)
        else:
            # Stopping Phase
            self.active = False
            self.btn_toggle.configure(text="...", text_color="#ff5555", state="disabled")
            self.transcript_line.configure(text="Stopping...", text_color="#ff5555")
            
            if self.stt:
                self.stt.stop()
                self.stt = None
            
            self.after(500, self.reset_ui_to_idle)

    def launch_stt_thread(self):
        try:
            self.stt = realtimeSTT(
                input_device_index=1, 
                partial_update=self.gui_partial_update,
                final_update=self.gui_final_update
            )
            threading.Thread(target=self.run_stt, daemon=True).start()
            
            self.btn_toggle.configure(text="■", text_color="#ff5555", state="normal")
            self.transcript_line.configure(text="Listening...", text_color=self.accent)
        except Exception as e:
            self.transcript_line.configure(text=f"ERROR: {str(e)}", text_color="#ff5555")
            self.reset_ui_to_idle()

    def reset_ui_to_idle(self):
        self.active = False
        self.btn_toggle.configure(text="▶", text_color=self.accent, state="normal")
        self.transcript_line.configure(text="Ready to assist.", text_color="#666")
        self.answer_box.configure(height=0)
        self.geometry("900x80")

    def gui_partial_update(self, text):
        display_text = text[-90:] if len(text) > 90 else text
        self.after(0, lambda: self.transcript_line.configure(text=f"• {display_text}", text_color="white"))

    async def gui_final_update(self, text):
        self.after(0, lambda: self.transcript_line.configure(text=f"Q: {text}", text_color=self.accent))
        res = await self.classifier.classify(text)
        if res.action == "respond":
            ans = await self.llm_generator.generate(question=text, intent=res.intent)
            self.after(0, self.show_ai_response, ans.text)

    def show_ai_response(self, text):
        self.geometry("900x220") 
        self.answer_box.configure(height=150)
        self.answer_box.delete("1.0", "end")
        self.answer_box.insert("1.0", text)

    def run_stt(self):
        if not self.stt: return
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.stt.start())
        except Exception: pass

    def on_closing(self):
        if self.stt: self.stt.stop()
        self.destroy()

if __name__ == "__main__":
    try:
        app = UltraMinimalHUD()
        app.mainloop()
    except KeyboardInterrupt:
        app.on_closing()