from PySide6.QtWidgets import QMessageBox
import os
from interface.ai.audio_transcriber import AudioTranscriber


class AudioManager:
    def __init__(self, app):
        self.app = app
        self.audio_transcriber = AudioTranscriber(app)

    def get_actions(self):
        return [
            {
                "name": "Convert to text",
                "action": self.convert_audio_to_text,
                "icon": self.app.icon_mapper.text_file_icon,
            }
        ]

    def convert_audio_to_text(self, file_path: str) -> bool:
        try:
            # Create the output file name
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_file = os.path.join(os.path.dirname(file_path), f"{base_name}.txt")

            # Use the AudioTranscriber to convert audio to text
            self.audio_transcriber.transcribe_audio_into_file(file_path, output_file)

            return False
        except Exception as e:
            QMessageBox.critical(
                self.app, "Error", f"Failed to convert audio to text: {str(e)}"
            )
            return False
