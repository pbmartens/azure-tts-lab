import os
import tempfile
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
from flask import Flask, request, render_template, Response, jsonify

load_dotenv()

app = Flask(__name__)

SPEECH_KEY = os.environ.get("SPEECH_KEY")
SPEECH_REGION = os.environ.get("SPEECH_REGION")
SPEECH_ENDPOINT = os.environ.get("SPEECH_ENDPOINT")

MAX_TEXT_LENGTH = 500
MAX_AUDIO_BYTES = 10 * 1024 * 1024


def get_speech_config():
    if SPEECH_ENDPOINT:
        return speechsdk.SpeechConfig(subscription=SPEECH_KEY, endpoint=SPEECH_ENDPOINT)
    return speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/synthesize", methods=["POST"])
def synthesize():
    text = (request.get_json(silent=True) or {}).get("text", "").strip()

    if not text:
        return jsonify({"error": "Please enter some text."}), 400
    if len(text) > MAX_TEXT_LENGTH:
        return jsonify({"error": f"Text too long (max {MAX_TEXT_LENGTH} characters)."}), 400

    speech_config = get_speech_config()
    speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
    )

    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return Response(result.audio_data, mimetype="audio/wav")

    if result.reason == speechsdk.ResultReason.Canceled:
        details = result.cancellation_details
        return jsonify({"error": f"Synthesis canceled: {details.reason}"}), 502

    return jsonify({"error": "Speech synthesis failed."}), 500


@app.route("/transcribe", methods=["POST"])
def transcribe():
    audio_file = request.files.get("audio")

    if not audio_file:
        return jsonify({"error": "No audio provided."}), 400

    audio_bytes = audio_file.read()
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        return jsonify({"error": "Audio too long."}), 400

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        speech_config = get_speech_config()
        audio_config = speechsdk.audio.AudioConfig(filename=tmp_path)
        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        result = recognizer.recognize_once()
    finally:
        os.remove(tmp_path)

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return jsonify({"text": result.text})

    if result.reason == speechsdk.ResultReason.NoMatch:
        return jsonify({"error": "Could not understand the audio."}), 422

    if result.reason == speechsdk.ResultReason.Canceled:
        details = result.cancellation_details
        return jsonify({"error": f"Recognition canceled: {details.reason}"}), 502

    return jsonify({"error": "Speech recognition failed."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
