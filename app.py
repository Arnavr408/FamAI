import os
import asyncio
import whisper
import sounddevice as sd
import numpy as np
import tempfile
import scipy.io.wavfile
import requests
from bs4 import BeautifulSoup
import time
import pyautogui
import pywhatkit as kit
from edge_tts import Communicate
import google.generativeai as genai
from vosk import Model, KaldiRecognizer
import json
from flask import Flask, render_template, request, jsonify
from threading import Thread

# 🔐 Gemini Setup
genai.configure(api_key="AIzaSyBRl1tbv45iW55dSN7g7u6_yQ12JYF7ebk")
model = genai.GenerativeModel("models/gemini-1.5-flash")

# 🎙️ Load Whisper
whisper_model = whisper.load_model("medium")

# 🎧 Output folder
STATIC_FOLDER = 'static'
if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)

# 🧠 Load Vosk model
vosk_model = Model("vosk-model-small-en-us-0.15")

# 🌐 Serper.dev Web Search
SERPER_API_KEY = "9221dffe133fa655d53dc21824a3c6a3669d6fb3"

# 🌐 Flask App
app = Flask(__name__, static_folder="static", template_folder="templates")

def search_web(query, num_results=3):
    print(f"🔍 Searching with Serper.dev: {query}")
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {"q": query, "num": num_results}
    try:
        response = requests.post("https://google.serper.dev/search", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return [
            {"title": item.get("title"), "href": item.get("link")}
            for item in data.get("organic", [])[:num_results]
        ]
    except Exception as e:
        print(f"(❌ Serper search failed: {e})")
        return []

def scrape_page(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        return "\n".join(p.get_text() for p in soup.find_all("p"))[:4000]
    except Exception as e:
        return f"(❌ Failed to scrape {url}: {e})"

def needs_web_search(query):
    prompt = f"Does this query require web search to answer it accurately? Reply ONLY with YES or NO.\nQuery: {query}"
    try:
        response = model.generate_content(prompt)
        return "yes" in response.text.strip().lower()
    except:
        return True

def is_session_done(query):
    prompt = f"Decide if this user query indicates the assistant session is finished. Reply ONLY YES or NO.\nQuery: {query}"
    try:
        response = model.generate_content(prompt)
        return "yes" in response.text.strip().lower()
    except:
        return False

def get_answer_from_web(query):
    results = search_web(query)
    if not results:
        return "No information found online."

    combined_text = ""
    for result in results:
        url = result.get("href") or result.get("url")
        if url:
            content = scrape_page(url)
            combined_text += f"\n--- From {url} ---\n{content}\n"

    prompt = f"Answer this question using the web info below:\n\nQuestion: {query}\n\nWeb Info:\n{combined_text}"
    response = model.generate_content(prompt)
    return response.text

async def speak(text):
    print("🔈 Speaking...")
    tts = Communicate(text=text, voice="en-US-AriaNeural")
    audio_filename = "output.mp3"
    audio_path = os.path.join(STATIC_FOLDER, audio_filename)
    await tts.save(audio_path)
    os.system(f"afplay '{audio_path}'")

def play_song(song_name):
    print(f"🎵 Playing song: {song_name}")
    kit.playonyt(song_name)
    time.sleep(5)
    pyautogui.press('space')

def record_audio(duration=5, fs=16000):
    print("🎤 Speak now...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    return audio, fs

def transcribe_audio():
    audio, fs = record_audio()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        scipy.io.wavfile.write(tmp.name, fs, audio)
        result = whisper_model.transcribe(tmp.name, language="en")
        os.unlink(tmp.name)
        return result["text"]

async def listen_for_wakeword():
    print("🕵️ Listening for wakeword...")
    recognizer = KaldiRecognizer(vosk_model, 16000)
    recognizer.SetWords(False)

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16', channels=1) as stream:
        while True:
            buffer, _ = stream.read(4000)
            audio_bytes = bytes(buffer)

            if recognizer.AcceptWaveform(audio_bytes):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").lower()
                print(f"🗣️ Heard: {text}")
                if "alexa" in text:
                    print("🎉 Wakeword detected!")
                    await speak("Yes? How can I help?")
                    return

async def assistant_session():
    while True:
        query = transcribe_audio()
        print(f"📝 You said: {query}")

        if "play" in query.lower():
            song_name = query.lower().replace("play", "").strip()
            play_song(song_name)
        else:
            if needs_web_search(query):
                answer = get_answer_from_web(query)
            else:
                answer = model.generate_content(query).text
            print(f"💡 Answer: {answer}")
            await speak(answer)

        if is_session_done(query):
            print("👋 Session complete. Returning to listening mode....")
            return

async def assistant_loop():
    while True:
        await listen_for_wakeword()
        await assistant_session()

def run_loop_in_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(assistant_loop())

# ------------------- FLASK ROUTES -------------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/wake", methods=["POST"])
def wake():
    thread = Thread(target=run_loop_in_thread)
    thread.start()
    return jsonify({"status": "Assistant activated"}), 200

@app.route("/stop", methods=["POST"])
def stop():
    # Placeholder: implement cancelation later if needed
    return jsonify({"status": "Stop pressed (no cancel logic yet)"}), 200

# ------------------ ENTRY POINT ---------------------

if __name__ == "__main__":
    app.run(debug=True)