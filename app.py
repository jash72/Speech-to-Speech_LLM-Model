from flask import Flask, request, render_template, send_file
import speech_recognition as sr
import pyttsx3
import google.generativeai as genai
from playsound import playsound
from gtts import gTTS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydub import AudioSegment

app = Flask(__name__)

genai.configure(api_key=GEN_AI_KEY)

generation_config = {
    "temperature": 2,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', 'voices[0].id')
#model = ChatGoogleGenerativeAI(google_api_key='', model="gemini-1.5-pro")


def speak(text):
    engine.say(text)
    engine.runAndWait()

def capture_audio(audio_file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file_path) as source:
        print("Listening...")
        audio = recognizer.listen(source)
        
        try:
            print("Recognizing...")
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            speak("Sorry, I could not understand the audio.")
            return True
        except sr.RequestError as e:
            speak(f"Could not request results; {e}")
            return True
    
def convert_ogg_to_wav(ogg_file_path, wav_file_path):
    audio = AudioSegment.from_ogg(ogg_file_path)
    audio.export(wav_file_path, format="wav")

'''
def speech_to_text(audio_file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file_path) as source:
        print("Processing audio...")
        audio = recognizer.record(source)
        text = recognizer.recognize_google(audio)
        return text
'''
#Using gTTS for converting Text to Speech
'''
def text_to_speech(text, response_audio_path="response.mp3"):
    tts = gTTS(text=text, lang='en')
    tts.save(response_audio_path)
    return response_audio_path
'''
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
