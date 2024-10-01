import os

try:
    from dotenv import load_dotenv
except ImportError:
    print(
        "python-dotenv is not installed. Please run 'pip install python-dotenv' to install it."
    )
    exit(1)

try:
    from flask import Flask, jsonify, request, Response
except ImportError:
    print("Flask is not installed. Please run 'pip install flask' to install it.")
    exit(1)

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part, SafetySetting, Content
except ImportError:
    print(
        "VertexAI is not installed. Please run 'pip install google-cloud-aiplatform' to install it."
    )
    exit(1)

import base64
from io import BytesIO
import time
from typing import List
import uuid
import json

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()


def package_messages(history):
    new_history = []
    for message in history:
        if message["role"] == "system":
            new_history += [
                Content(
                    parts=[Part.from_text("SYSTEM MESSAGE: " + message["content"])],
                    role="user",
                ),
                Content(
                    parts=[Part.from_text(message["content"])],
                    role="assistant",
                ),
            ]
        else:
            new_history += [
                Content(
                    parts=[Part.from_text(message["content"])], role=message["role"]
                )
            ]
    return new_history


@app.route("/chat/completions", methods=["POST"])
def chat_completions():
    data = request.json
    conversation = data.get("messages", [])

    # Load project from environment variable
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    vertexai.init(project=project, location="europe-west4")
    model = GenerativeModel(
        "gemini-1.5-flash-002",
    )

    # Separate the last message from the conversation
    history = conversation[:-1]
    last_message = conversation[-1] if conversation else None

    # Convert history to Part objects
    history: List[Content] = package_messages(history)

    chat = model.start_chat(history=history)

    # Send the last message using chat.send_message
    if last_message:
        response = chat.send_message(last_message["content"])
        assistant_response = response.text
    else:
        assistant_response = "No message provided."

    response = {
        "id": f"chatcmpl-{uuid.uuid4()}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": data.get("model", "gpt-3.5-turbo"),
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": assistant_response,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
    }

    return jsonify(response)


@app.route("/images/generations", methods=["POST"])
def images_generations():
    data = request.json
    image_id = str(uuid.uuid4())

    # Generate a dummy image (1x1 pixel, base64 encoded)
    dummy_image = base64.b64encode(b"\x00\x00\x00").decode("utf-8")

    images[image_id] = {
        "prompt": data.get("prompt"),
        "size": data.get("size", "1024x1024"),
        "image": dummy_image,
    }

    response = {"created": int(time.time()), "data": [{"b64_json": dummy_image}]}

    return jsonify(response)


@app.route("/audio/transcriptions", methods=["POST"])
def transcribe_audio():
    file = request.files.get("file")

    if not file:
        return jsonify({"error": "No file provided"}), 400

    # Dummy transcription
    transcription = "This is a dummy transcription from the Gemini server."

    return jsonify({"text": transcription})


@app.route("/audio/speech", methods=["POST"])
def text_to_speech():
    data = request.json
    text = data.get("input")

    if not text:
        return jsonify({"error": "No input text provided"}), 400

    # Generate dummy audio data (1 second of silence)
    dummy_audio = b"\x00" * 44100 * 2  # 1 second of 16-bit silence at 44.1kHz

    return Response(dummy_audio, mimetype="audio/wav")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=17171)
