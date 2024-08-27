from flask import Flask, request, render_template, send_file
import speech_recognition as sr
from gtts import gTTS
import os
from playsound import playsound
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydub import AudioSegment

app = Flask(__name__)

model = ChatGoogleGenerativeAI(google_api_key='AIzaSyBphwpVRij2r40swh6GOu3md5PD1bXRpT4', model="gemini-1.5-pro")

def convert_ogg_to_wav(ogg_file_path, wav_file_path):
    audio = AudioSegment.from_ogg(ogg_file_path)
    audio.export(wav_file_path, format="wav")

def speech_to_text(audio_file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file_path) as source:
        print("Processing audio...")
        audio = recognizer.record(source)
        text = recognizer.recognize_google(audio)
        return text

def text_to_speech(text, response_audio_path="response.mp3"):
    tts = gTTS(text=text, lang='en')
    tts.save(response_audio_path)
    return response_audio_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    if 'audio_data' not in request.files:
        return "No audio file provided", 400

    audio_file = request.files['audio_data']
    audio_file_path = 'uploaded_audio.ogg'
    wav_file_path = 'converted_audio.wav'
    audio_file.save(audio_file_path)

    # Convert OGG to WAV
    convert_ogg_to_wav(audio_file_path, wav_file_path)

    try:
        text = speech_to_text(wav_file_path)
    except Exception as e:
        return str(e), 500

    messages = [
        SystemMessage(content="You are my personal assistant. Provide concise explanations."),
        HumanMessage(content=text)
    ]

    response_text = model.invoke(messages).content

    response_audio_path = text_to_speech(response_text)
    return send_file(response_audio_path, as_attachment=True, download_name='response.mp3')

if __name__ == "__main__":
    app.run(debug=True)
