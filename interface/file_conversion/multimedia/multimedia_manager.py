from PySide6.QtWidgets import QMessageBox
import os
from interface.ai.audio_transcriber import AudioTranscriber
from interface.file_conversion.multimedia.ffmpeg_handler import FfmpegHandler


class MultimediaManager:
    def __init__(self, app):
        self.app = app
        self.audio_transcriber = AudioTranscriber(app)
        self.ffmpeg_handler = FfmpegHandler(app)

    def get_actions(self, file_extension: str):
        actions = [
            {
                "name": "Convert to text",
                "action": self.convert_audio_to_text,
                "icon": self.app.icon_mapper.text_file_icon,
                "ai_only": True,
            }
        ]

        if file_extension in (".mp3", ".wav", ".flac", ".m4a"):
            return actions

        if file_extension in (".mp4", ".mov", ".avi", ".mkv"):
            video_actions = []
            if self.ffmpeg_handler.is_ffmpeg_available():
                video_actions.append(
                    {
                        "name": "Convert to audio",
                        "action": self.convert_video_to_audio,
                        "icon": self.app.icon_mapper.audio_file_icon,
                        "ai_only": False,
                    }
                )
            return video_actions + actions
        else:
            return []

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

    def convert_video_to_audio(self, file_path: str) -> bool:
        try:
            self.ffmpeg_handler.convert_video_to_audio(file_path)
            return True
        except Exception as e:
            QMessageBox.critical(
                self.app, "Error", f"Failed to convert video to audio: {str(e)}"
            )
            return False
