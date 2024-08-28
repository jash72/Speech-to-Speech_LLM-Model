from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
import pyttsx3
import google.generativeai as genai
import datetime
import os
import threading

app = Flask(__name__)

genai.configure(api_key=GEN_KEY)

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
engine.setProperty('voice', voices[0].id)

def speak(text):
    engine.say(text)
    engine.runAndWait()
    
def speak_async(text):
    def task():
        speak(text)
    thread = threading.Thread(target=task)
    thread.start()

def capture_audio_from_file(file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        print("Listening to the audio file...")
        audio = recognizer.record(source)

        try:
            print("Recognizing...")
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            speak_async("Sorry, I could not understand the audio, please say that again.")
            return "error"
        except sr.RequestError as e:
            speak_async("Could not request results. Pardon me, please say that again.")
            return "error"

chat_history = [
    {
        "role": "user",
        "parts": [
            "your name is Tensy an AI voice assistant, you answer all questions shortly correctly.\n",
        ],
    },
    {
        "role": "model",
        "parts": [
            "Okay, I understand. Ask me anything and I'll answer concisely and accurately. 😊\n",
        ],
    },
]

chat_session = model.start_chat(history=chat_history)

def process_response(response_text):
    clean_text = response_text.replace('**', '').replace('*', '')
    return clean_text

def continue_chat(user_message):
    response = chat_session.send_message(user_message)
    clean_response_text = process_response(response.text)
    chat_history.append({
        "role": "user",
        "parts": [user_message]
    })
    chat_history.append({
        "role": "model",
        "parts": [clean_response_text]
    })

    print("AI: ", clean_response_text)
    speak_async(clean_response_text)
    return clean_response_text

def intro():
    hour = datetime.datetime.now().hour
    if hour >= 0 and hour < 12:
        wish = "Hello, Good Morning"
    elif hour >= 12 and hour < 18:
        wish = "Hello, Good Afternoon"
    else:
        wish = "Hello, Good Evening"

    intro_message = wish + " My Name is Tensy, Tell me how can I assist you!"
    speak_async(intro_message)
    return intro_message

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/greeting')
def greeting():
    intro_message = intro()
    return jsonify({'greeting': intro_message})

@app.route('/process_audio', methods=['POST'])
def process_audio():
    if 'audio_file' not in request.files:
        return jsonify({'response': 'No audio found.'}), 400

    audio_file = request.files['audio_file']
    file_path = os.path.join('uploads', audio_file.filename)
    audio_file.save(file_path)

    text = capture_audio_from_file(file_path)
    if text == "error":
        return jsonify({'response': 'Sorry, I did not catch that. Please try again.'})

    response_text = continue_chat(text)
    os.remove(file_path)
    return jsonify({'response': response_text})

if __name__ == "__main__":
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
