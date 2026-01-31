# Interview Copilot

Realtime audio capture + speech-to-text + NLP intent classification + optional LLM answer generation for interview assistance.

---

## Setup & Run

1. Download a model from **https://alphacephei.com/vosk/models**, create a folder named **models**, and unzip the model there.
2. Install dependencies:
   - `pip install -r requirements`
3. Run `audio_devices.py` to get input/output device indexes.
4. In `main.py`, set:
   - `MODEL_PATH`
   - `MIC_DEVICE_INDEX` (or `DEVICE_INDEX` if you use a single device)
   - `SYS_DEVICE_INDEX`
5. Set `groq_api_key` in `.env`.
6. Run:
   - `python main.py`

---

## Project Structure

```
interview copilot/
├─ audio_capture/
│  └─ capture.py          # Captures audio input and streams frames into async queues
├─ stt/
│  ├─ vosk_stt.py          # Vosk-based speech-to-text pipeline
│  ├─ silero_vad.py        # Voice activity detection helpers
│  └─ audio_utils.py       # Audio format utilities
├─ nlp/
│  ├─ classifier.py        # High-level NLP classifier
│  ├─ nlp_classifier.py    # Implementation details for classification
│  ├─ classifier_types.py  # Type definitions for classifier outputs
│  ├─ confidence.py        # Confidence scoring utilities
│  ├─ question_event.py    # Question event dataclass/model
│  └─ utterance_aggregator.py
├─ answers/
│  ├─ llm_answer_generation.py  # LLM answer generation
│  └─ llm_types.py              # LLM response types
├─ models/                 # Vosk models (unzipped here)
├─ audio_devices.py        # Lists audio devices and indexes
├─ main.py                 # App entrypoint (mic + system audio)
├─ trigger_test.py         # NLP + LLM test runner
├─ requirements            # Dependency spec
└─ .env                    # Environment variables (groq_api_key)
```

---

## How It Works (High Level)

1. **Audio Capture**  
   `audio_capture.capture.AudioCapture` opens an input device and streams frames into an async queue.

2. **Speech-to-Text (STT)**  
   `stt.vosk_stt.VoskSTT` consumes audio frames, runs Vosk recognition, and emits transcripts.

3. **NLP Classification**  
   NLP modules detect interview questions and intents using confidence scoring + classifier logic.

4. **Answer Generation (Optional)**  
   `answers.llm_answer_generation.LLMAnswerGenerator` can expand an answer using the configured LLM API key.

---

## Common Tasks

### List audio devices
```
python audio_devices.py
```

### Test NLP + LLM
```
python trigger_test.py
```

---

## Notes

- Ensure your **Vosk model path** in `main.py` matches the unzipped folder name.
- On Windows, device indexes can change between reboots—recheck with `audio_devices.py` if audio fails.