import os
import base64
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QGraphicsView,
    QGraphicsScene,
    QTextEdit,
)
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, QObject, Signal, QThread
from interface.ai.openai_client import OpenAIClient

from interface.constants import settings


class ImageGeneratorWorker(QObject):
    finished = Signal(QImage)
    error = Signal(str)

    def __init__(self, client, prompt):
        super().__init__()
        self.client = client
        self.prompt = prompt

    def run(self):
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=self.prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            image_b64 = response.data[0].b64_json
            image_data = base64.b64decode(image_b64)
            generated_image = QImage.fromData(image_data)
            self.finished.emit(generated_image)
        except Exception as e:
            self.error.emit(str(e))


class ImageGenerator:
    def __init__(self, app):
        self.app = app
        self.dialog = None

    def generate_image(self, name, prompt, save_path):
        client = OpenAIClient(
            api_key=settings.value("api_key", ""),
            base_url=settings.value("custom_url", "https://api.openai.com/v1"),
        )

        if not client.check_api_access(self.app):
            self.dialog.close()
            return

        self.worker = ImageGeneratorWorker(client, prompt)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.handle_generated_image)
        self.worker.error.connect(self.handle_generation_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

        # Disable the generate button and show a loading indicator
        self.generate_button.setEnabled(False)
        self.generate_button.setText("Generating...")

    def handle_generated_image(self, generated_image):
        self.generated_image = generated_image
        pixmap = QPixmap.fromImage(self.generated_image)
        self.preview_scene.clear()
        self.preview_scene.addPixmap(pixmap)
        self.preview_view.fitInView(self.preview_scene.sceneRect(), Qt.KeepAspectRatio)
        self.save_button.setEnabled(True)
        self.generate_button.setEnabled(True)
        self.generate_button.setText("Generate")

    def handle_generation_error(self, error_message):
        QMessageBox.critical(
            self.app, "Error", f"Error generating image: {error_message}"
        )
        self.generate_button.setEnabled(True)
        self.generate_button.setText("Generate")

    def show_generate_image_dialog(self, parent, current_path):
        if self.dialog is None:
            self.dialog = QDialog(parent)
            self.dialog.setWindowTitle("Generate Image")
            layout = QVBoxLayout()

            # Add preview image
            self.preview_view = QGraphicsView()
            self.preview_scene = QGraphicsScene()
            self.preview_view.setScene(self.preview_scene)
            self.preview_view.setFixedSize(400, 400)
            layout.addWidget(self.preview_view)

            # Add file name input
            name_layout = QHBoxLayout()
            name_label = QLabel("Name:")
            self.name_input = QLineEdit()
            name_layout.addWidget(name_label)
            name_layout.addWidget(self.name_input)
            layout.addLayout(name_layout)

            # Add prompt input (multiline)
            prompt_label = QLabel("Prompt:")
            self.prompt_input = QTextEdit()
            self.prompt_input.setFixedHeight(100)
            layout.addWidget(prompt_label)
            layout.addWidget(self.prompt_input)

            # Add buttons
            button_layout = QHBoxLayout()
            self.generate_button = QPushButton("Generate")
            self.save_button = QPushButton("Save")
            self.save_button.setEnabled(False)
            cancel_button = QPushButton("Cancel")
            button_layout.addWidget(self.generate_button)
            button_layout.addWidget(self.save_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)

            self.dialog.setLayout(layout)

            self.generate_button.clicked.connect(self.on_generate)
            self.save_button.clicked.connect(self.on_save)
            cancel_button.clicked.connect(self.dialog.reject)
            self.dialog.finished.connect(self.on_dialog_closed)

        self.current_path = current_path
        self.generated_image = None

        self.dialog.show()  # Use show() instead of exec()

    def on_generate(self):
        name = self.name_input.text()
        prompt = self.prompt_input.toPlainText()
        if name and prompt:
            self.generate_image(name, prompt, self.current_path)

    def on_save(self):
        if self.generated_image:
            file_path = os.path.join(self.current_path, f"{self.name_input.text()}.png")
            self.generated_image.save(file_path, "PNG")
            print(f"Image saved as: {file_path}")
            self.app.update_view()  # Refresh the file explorer view
            self.dialog.accept()

    def on_dialog_closed(self):
        self.dialog = None
