import subprocess
import shutil
import os
from PySide6.QtWidgets import QMessageBox


class FfmpegHandler:
    def __init__(self, app):
        self.app = app
        self.ffmpeg_path = self._find_ffmpeg()

    def _find_ffmpeg(self):
        return shutil.which("ffmpeg")

    def is_ffmpeg_available(self):
        return self.ffmpeg_path is not None

    def convert_video_to_audio(self, input_file: str) -> str:
        if not self.is_ffmpeg_available():
            QMessageBox.critical(
                self.app, "Error", "FFmpeg is not available on the system."
            )
            return None

        output_file = os.path.splitext(input_file)[0] + ".mp3"

        print(self.ffmpeg_path, input_file, output_file)

        try:
            subprocess.run(
                [self.ffmpeg_path, "-i", input_file, output_file],
                check=True,
                capture_output=True,
                text=True,
            )
            return output_file
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(
                self.app, "Error", f"FFmpeg conversion failed: {e.stderr}"
            )
            return None
