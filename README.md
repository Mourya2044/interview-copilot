# Interview Copilot

**Interview Copilot** is a high-performance, real-time AI assistant built to support candidates during interviews. By transcribing audio on the fly and generating concise, professional answers using state-of-the-art LLMs via the Groq API, it provides a seamless second-brain experience for technical and behavioral assessments.

---

## Key Features

- **Stealth Overlay Mode**: A modern, semi-transparent GUI that floats on top of all windows and is **excluded from screen capture** (invisible to Zoom, Microsoft Teams, and other recording software).
- **Click-Through Technology**: The overlay becomes click-through during active sessions, allowing you to interact with other applications while keeping the AI suggestions in view.
- **Low-Latency Transcription**: Powered by `RealtimeSTT` (utilizing `faster-whisper`) for near-instant speech recognition.
- **Intelligent Intent Classification**: Automatically distinguishes between interviewer questions, conversational filler, and background noise.
- **Context-Aware Responses**: Generates 2-3 sentence answers tailored for verbal interviews, maintaining a rolling conversation history for follow-ups.
- **Optimized Inference**: Leverages Groq's high-speed cloud infrastructure for sub-second LLM responses.

---

## Technical Stack

- **GUI Framework**: [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- **STT Engine**: [RealtimeSTT](https://github.com/KoljaB/RealtimeSTT) (`faster-whisper`)
- **LLM Provider**: [Groq Cloud SDK](https://console.groq.com/)
- **Audio Backend**: PyAudio
- **Stealth Features**: Win32 API integration (`WDA_EXCLUDEFROMCAPTURE`, `WS_EX_TOOLWINDOW`, `WS_EX_APPWINDOW`)

---

## Installation and Setup

### 1. Prerequisites
- **Python 3.9+**
- **FFmpeg**: Required for audio processing.
    - *Windows*: `choco install ffmpeg`
    - *macOS*: `brew install ffmpeg`
- **PortAudio**: Required for PyAudio (if not pre-installed).

### 2. Clone and Install
```bash
git clone <repository-url>
cd "interview copilot"
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```

---

## Usage

### Option A: Stealth Overlay (Recommended)
Launch the modern GUI with stealth features:
```bash
python gui.py
```
- **Select Microphone**: Choose your audio input from the dropdown menu.
- **Start Session**: Begins the STT-NLP pipeline. The window becomes click-through and invisible to screen captures.
- **Interact**: Hover over the sidebar to re-enable mouse interaction.

### Option B: Command Line Interface
Launch the terminal-based assistant:
```bash
python main.py
```
- Follow the prompt to select your microphone device index.
- Transcripts and AI answers will be printed directly in the console.

---

## Project Structure

- `gui.py`: The modern stealth overlay with click-through and capture-blocking logic.
- `main.py`: The central CLI orchestrator for the STT-NLP-LLM pipeline.
- `audio_devices.py`: Utility script to list available audio input indices.
- `stt/`: Contains the `RealtimeSTT` integration and configuration.
- `nlp/`:
    - `classifier.py`: LLM-based logic for identifying speech intent and actions.
    - `answer_generation.py`: Prompt engineering and response generation logic.

---

## Disclaimer

This tool is designed for educational and preparation purposes. Use of this assistant during an actual interview may violate the terms of the interview process or company policy. Users are responsible for ensuring compliance with all applicable rules and ethical guidelines.
