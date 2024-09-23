import os
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QMessageBox,
)
from PySide6.QtCore import QObject, Signal, QThread
from interface.ai.openai_client import OpenAIClient


class SpeechGeneratorWorker(QObject):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, client, text, output_path, voice):
        super().__init__()
        self.client = client
        self.text = text
        self.voice = voice
        self.output_path = output_path

    def run(self):
        try:
            response = self.client.audio.speech.create(
                model="tts-1", voice=self.voice, input=self.text
            )
            response.stream_to_file(self.output_path)
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))


class SpeechGenerator:
    def __init__(self, app):
        self.app = app
        self.client = OpenAIClient(api_key="test", base_url="http://localhost:17173")
        self.dialog = None

    def generate_speech(self, text, output_path, voice):
        self.worker = SpeechGeneratorWorker(self.client, text, output_path, voice)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.handle_generated_speech)
        self.worker.error.connect(self.handle_generation_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

        self.generate_button.setEnabled(False)
        self.generate_button.setText("Generating...")

    def handle_generated_speech(self, output_path):
        print(f"Speech saved as: {output_path}")
        self.app.update_view()
        self.generate_button.setEnabled(True)
        self.generate_button.setText("Generate")
        self.dialog.accept()

    def handle_generation_error(self, error_message):
        QMessageBox.critical(
            self.app, "Error", f"Error generating speech: {error_message}"
        )
        self.generate_button.setEnabled(True)
        self.generate_button.setText("Generate")

    def show_generate_speech_dialog(self, file_path, output_path):
        self.file_path = file_path
        self.output_path = output_path
        self.file_name = os.path.splitext(os.path.basename(file_path))[0]

        if self.dialog is None:
            self.dialog = QDialog(self.app)
            self.dialog.setWindowTitle("Generate Speech")
            layout = QVBoxLayout()

            voice_layout = QHBoxLayout()
            voice_label = QLabel("Voice:")
            self.voice_combo = QComboBox()
            self.voice_combo.addItems(
                ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            )
            voice_layout.addWidget(voice_label)
            voice_layout.addWidget(self.voice_combo)
            layout.addLayout(voice_layout)

            button_layout = QHBoxLayout()
            self.generate_button = QPushButton("Generate")
            close_button = QPushButton("Close")
            button_layout.addWidget(self.generate_button)
            button_layout.addWidget(close_button)
            layout.addLayout(button_layout)

            self.dialog.setLayout(layout)

            self.generate_button.clicked.connect(self.on_generate)
            close_button.clicked.connect(self.on_dialog_close)
            self.dialog.finished.connect(self.on_dialog_close)

        self.dialog.show()

    def on_generate(self):
        with open(self.file_path, "r", encoding="utf-8") as file:
            text = file.read()
        voice = self.voice_combo.currentText()
        output_path = os.path.join(self.output_path, f"{self.file_name}.wav")
        self.generate_speech(text, output_path, voice)

    def on_dialog_close(self):
        self.dialog = None
