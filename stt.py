import whisper
import sounddevice as sd
import numpy as np
import tempfile
import os
import scipy.io.wavfile

model = whisper.load_model("medium")  # or "large" if you're feeling fancy

def record_audio(duration=5, fs=16000):
    print("🎙️ Recording...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    return audio, fs

def transcribe_audio():
    audio, fs = record_audio()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        scipy.io.wavfile.write(tmp.name, fs, audio)
        result = model.transcribe(tmp.name)
        os.unlink(tmp.name)
        return result["text"]

if __name__ == "__main__":
    print("🔄 Listening...")
    text = transcribe_audio()
    print("📝 You said:", text)
