const mic_btn = document.querySelector("#mic");
const playback = document.querySelector(".playback");

mic_btn.addEventListener("click", ToggleMic);

let can_record = false;
let is_recording = false;
let recorder = null;
let chunks = [];

function SetupAudio() {
    console.log("Setup");
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices
            .getUserMedia({ audio: true })
            .then(SetupStream)
            .catch(err => {
                console.error("Error accessing microphone:", err);
            });
    } else {
        console.error("getUserMedia not supported on your browser!");
    }
}

SetupAudio();

function SetupStream(stream) {
    recorder = new MediaRecorder(stream);

    recorder.ondataavailable = e => {
        chunks.push(e.data);
    }

    recorder.onstop = e => {
        const blob = new Blob(chunks, { type: "audio/ogg; codecs=opus" });
        chunks = [];
        
        SendAudioToServer(blob);
    }

    can_record = true;
}

function ToggleMic() {
    if (!can_record) return;

    is_recording = !is_recording;

    if (is_recording) {
        recorder.start();
        mic_btn.classList.add("is-recording");
    } else {
        recorder.stop();
        mic_btn.classList.remove("is-recording");
    }
}

function SendAudioToServer(blob) {
    const formData = new FormData();
    formData.append("audio_data", blob, "recording.ogg");

    fetch('/upload_audio', {
        method: 'POST',
        body: formData
    })
    .then(response => response.blob())
    .then(blob => {
        const audioURL = window.URL.createObjectURL(blob);
        playback.src = audioURL; 
        playback.play();
    })
    .catch(error => {
        console.error("Error sending audio to server:", error);
    });
}