from PySide6.QtWidgets import QMessageBox
import os
from interface.ai.speech_generator import SpeechGenerator


class TextManager:
    def __init__(self, app):
        self.app = app
        self.speech_generator = SpeechGenerator(app)

    def get_actions(self):
        return [
            {
                "name": "Convert to Audio",
                "action": self.convert_text_to_audio,
                "icon": self.app.icon_mapper.audio_file_icon,
                "ai_only": True,
            }
        ]

    def convert_text_to_audio(self, file_path: str) -> bool:
        try:
            output_path = os.path.dirname(file_path)
            self.speech_generator.show_generate_speech_dialog(file_path, output_path)
            return True
        except Exception as e:
            QMessageBox.critical(
                self.app, "Error", f"Failed to convert text to audio: {str(e)}"
            )
            return False
