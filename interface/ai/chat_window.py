from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
)
from PySide6.QtCore import Qt
from interface.ai.openai_client import OpenAIClient

from interface.constants import settings


class ChatWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle("AI Chat")
        self.setGeometry(200, 200, 600, 400)

        layout = QVBoxLayout()

        # Chat history display
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        layout.addWidget(self.chat_history)

        # User input area
        self.user_input = QTextEdit()
        self.user_input.setFixedHeight(100)
        layout.addWidget(self.user_input)

        # Send button
        button_layout = QHBoxLayout()
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        button_layout.addStretch()
        button_layout.addWidget(self.send_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.messages = []

    def send_message(self):
        openai_client = OpenAIClient(
            settings.value("api_key", ""),
            settings.value("custom_url", "https://api.openai.com/v1"),
        )

        user_message = self.user_input.toPlainText().strip()
        if user_message:
            self.messages.append({"role": "user", "content": user_message})
            self.chat_history.append(f"You: {user_message}")
            self.user_input.clear()

            response = openai_client.chat_completion(self.messages)
            ai_message = response["choices"][0]["message"]["content"]
            self.messages.append({"role": "assistant", "content": ai_message})
            self.chat_history.append(f"AI: {ai_message}")

    def position_window(self):
        parent_geometry = self.parent.geometry()
        self.setGeometry(
            parent_geometry.right(),
            parent_geometry.top(),
            self.width(),
            parent_geometry.height(),
        )

    def showEvent(self, event):
        super().showEvent(event)
        self.position_window()
