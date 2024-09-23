import requests
from PySide6.QtWidgets import QMessageBox


class OpenAIClient:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.audio = Audio(self)
        self.images = Images(self)

    def check_api_access(self, parent):
        print(self.base_url, self.api_key)
        if self.base_url == "https://api.openai.com/v1" and not self.api_key:
            QMessageBox.warning(
                parent,
                "API Key Required",
                "You need to create an API key to use OpenAI services.",
            )
            return False
        return True

    def chat_completion(self, messages):

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
        }
        response = requests.post(
            f"{self.base_url}/v1/chat/completions", headers=headers, json=data
        )
        return response.json()


class Audio:
    def __init__(self, client):
        self.client = client
        self.speech = Speech(client)
        self.transcriptions = Transcriptions(client)


class Transcriptions:
    def __init__(self, client):
        self.client = client

    def create(self, model, file):
        headers = {
            "Authorization": f"Bearer {self.client.api_key}",
        }
        files = {
            "file": file,
        }
        data = {
            "model": model,
        }
        response = requests.post(
            f"{self.client.base_url}/audio/transcriptions",
            headers=headers,
            files=files,
            data=data,
        )
        return TranscriptionResponse(response.json())


class TranscriptionResponse:
    def __init__(self, response_data):
        self.text = response_data.get("text", "")


class AudioResponse:
    def __init__(self, response):
        self.response = response

    def stream_to_file(self, output_path):
        with open(output_path, "wb") as f:
            for chunk in self.response.iter_content(chunk_size=8192):
                f.write(chunk)


class Speech:
    def __init__(self, client):
        self.client = client

    def create(self, model, voice, input):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.client.api_key}",
        }
        data = {
            "model": model,
            "voice": voice,
            "input": input,
        }
        response = requests.post(
            f"{self.client.base_url}/audio/speech",
            headers=headers,
            json=data,
            stream=True,
        )
        return AudioResponse(response)


class Images:
    def __init__(self, client):
        self.client = client

    def generate(self, model, prompt, size, quality, n):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.client.api_key}",
        }
        data = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": n,
        }
        response = requests.post(
            f"{self.client.base_url}/images/generations",
            headers=headers,
            json=data,
        )
        return ImageResponse(response.json())


class ImageResponse:
    def __init__(self, response_data):
        self.data = [ImageData(item) for item in response_data.get("data", [])]


class ImageData:
    def __init__(self, data):
        self.b64_json = data.get("b64_json")
