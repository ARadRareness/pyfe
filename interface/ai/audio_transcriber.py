from PySide6.QtWidgets import QMessageBox, QLabel
from PySide6.QtCore import QObject, Signal, QThread, Qt

from interface.ai.openai_client import OpenAIClient

from interface.constants import settings


class AudioTranscriberWorker(QObject):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, client, input_file_path, output_file_path):
        super().__init__()
        self.client = client
        self.input_file_path = input_file_path
        self.output_file_path = output_file_path

    def run(self):
        try:
            with open(self.input_file_path, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    model="whisper-1", file=audio_file
                )

            with open(self.output_file_path, "w", encoding="utf-8") as output_file:
                output_file.write(transcription.text)

            self.finished.emit(self.output_file_path)
        except Exception as e:
            self.error.emit(str(e))


class AudioTranscriber:
    def __init__(self, app):
        self.app = app
        self.msg_label = None

    def transcribe_audio_into_file(self, input_file_path, output_file_path):
        # Show a non-modal "Transcribing..." message
        self.msg_label = QLabel("Transcribing audio file...", self.app)
        self.msg_label.setAlignment(Qt.AlignCenter)
        self.msg_label.setStyleSheet(
            "background-color: #f0f0f0; padding: 10px; border: 1px solid #cccccc;"
        )
        self.msg_label.setWindowFlags(
            Qt.Window  # | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.msg_label.show()

        client = OpenAIClient(
            api_key=settings.value("api_key", ""),
            base_url=settings.value("custom_url", "https://api.openai.com/v1"),
        )

        if not client.check_api_access(self.app):
            self.close_msg()
            return

        # Create and start the worker thread
        self.worker = AudioTranscriberWorker(client, input_file_path, output_file_path)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.handle_transcription)
        self.worker.error.connect(self.handle_transcription_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.error.connect(self.thread.quit)
        self.worker.error.connect(self.worker.deleteLater)
        self.thread.start()

    def handle_transcription(self, output_file_path):
        print(f"Transcription completed and saved to: {output_file_path}")
        self.app.update_view()
        self.close_msg()

    def handle_transcription_error(self, error_message):
        self.close_msg()  # Close the message box first
        QMessageBox.critical(
            self.app, "Error", f"Error transcribing audio: {error_message}"
        )

    def close_msg(self):
        if self.msg_label:
            self.msg_label.close()
            self.msg_label = None
