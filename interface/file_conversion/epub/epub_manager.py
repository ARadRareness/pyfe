from PySide6.QtWidgets import QMessageBox
import os
from interface.file_conversion.epub.epub_lib import load_epub


class EpubManager:
    def __init__(self, app):
        self.app = app

    def get_actions(self):
        return [
            {
                "name": "Convert to text",
                "action": self.convert_epub_to_text,
                "icon": self.app.icon_mapper.text_file_icon,
                "ai_only": False,
            }
        ]

    def convert_epub_to_text(self, file_path: str) -> bool:
        try:
            # Load the EPUB content
            epub_content = load_epub(file_path)

            # Create the output file name
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_file = os.path.join(os.path.dirname(file_path), f"{base_name}.txt")

            # Write the content to the text file
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(epub_content)

            return True
        except Exception as e:
            QMessageBox.critical(
                self.app, "Error", f"Failed to convert EPUB to text: {str(e)}"
            )
            return False
