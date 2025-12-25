import asyncio
import whisper
import sounddevice as sd
import numpy as np
import tempfile
import os
import scipy.io.wavfile
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import google.generativeai as genai
from edge_tts import Communicate
import pywhatkit as kit
import time
import pyautogui
import pvporcupine
import pyaudio

# 🔐 Configure Gemini
genai.configure(api_key="AIzaSyBNQEbWt-je18Gb8mBou9jbxIeeQckl--I")
model = genai.GenerativeModel("models/gemini-1.5-pro-latest")

# 🎙️ Whisper STT
whisper_model = whisper.load_model("medium")  # or "large"

def record_audio(duration=5, fs=16000):
    print("🎤 Speak now...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    return audio, fs

def transcribe_audio():
    audio, fs = record_audio()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        scipy.io.wavfile.write(tmp.name, fs, audio)
        result = whisper_model.transcribe(tmp.name)
        os.unlink(tmp.name)
        return result["text"]

# 🌐 Web Search + Scrape
def search_web(query, num_results=3):
    print(f"🔍 Searching DuckDuckGo for: {query}")
    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=num_results))

def scrape_page(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        return "\n".join(p.get_text() for p in soup.find_all("p"))[:4000]
    except Exception as e:
        return f"(❌ Failed to scrape {url}: {e})"

# 🧠 Get Gemini Answer
def get_answer_from_web(query):
    results = search_web(query)
    if not results:
        return "No info found."

    combined_text = ""
    for result in results:
        url = result.get("href") or result.get("url")
        if url:
            content = scrape_page(url)
            combined_text += f"\n--- From {url} ---\n{content}\n"

    prompt = f"Answer this question using the web info below:\n\nQuestion: {query}\n\nWeb Info:\n{combined_text}"
    response = model.generate_content(prompt)
    return response.text

# 🔊 Edge TTS
async def speak(text):
    print(f"🔈 Speaking...")
    tts = Communicate(text=text, voice="en-US-AriaNeural")
    await tts.save("output.mp3")
    os.system("afplay output.mp3")  # Mac-specific audio playback

# 🧩 Play YouTube Song
def play_song(song_name):
    print(f"🎵 Playing song: {song_name}")
    kit.playonyt(song_name)
    
    # Wait for the browser to open and load the video
    time.sleep(5)  # Adjust the sleep time as needed

    # Simulate pressing the spacebar to start the video
    pyautogui.press('space')
    print(f"🎶 {song_name} is now playing.")

# 🧩 Listen for Wakeword (Async version)
async def listen_for_wakeword():
    access_key = "z8d55eg3c++VA9eENl8F+dQ3ML7k9ZRt0Gl2AfRAsggjf/vTLvMQoA=="  # Replace with your actual access key
    
    # Specify the path to your custom .ppn model file
    model_path = "/Users/chetanyadwadkar/Documents/FamAI/Hey-Alexa_en_mac_v3_0_0/Hey-Alexa_en_mac_v3_0_0.ppn"  # Replace this with the actual path to your .ppn file

    # Create the Porcupine instance using the path to your custom model via keyword_paths
    porcupine = pvporcupine.create(keyword_paths=[model_path], access_key=access_key)

    pyaudio_instance = pyaudio.PyAudio()
    stream = pyaudio_instance.open(rate=porcupine.sample_rate,
                                    channels=1,
                                    format=pyaudio.paInt16,
                                    input=True,
                                    frames_per_buffer=porcupine.frame_length)

    print("⏳ Waiting for custom wakeword...")
    while True:
        pcm = stream.read(porcupine.frame_length)
        pcm = np.frombuffer(pcm, dtype=np.int16)
        result = porcupine.process(pcm)
        if result >= 0:
            print("🎉 Wakeword detected! Triggering the assistant...")
            # Respond with "Hey, how can I help you?"
            await speak("Hey, how can I help you?")
            return True


# 🧩 Main Logic (Async version)
async def main():
    while True:
        if await listen_for_wakeword():  # Wait for the wakeword detection asynchronously
            print("🌀 Ready! Ask your question...")
            query = transcribe_audio()
            print(f"📝 You said: {query}")
            
            if "play" in query.lower():  # Check if the user wants to play a song
                song_name = query.lower().replace("play", "").strip()
                play_song(song_name)
            else:
                answer = get_answer_from_web(query)
                print(f"💡 Answer: {answer}")
                await speak(answer)

if __name__ == "__main__":
    asyncio.run(main())
