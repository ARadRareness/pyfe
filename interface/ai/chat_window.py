from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
    QCheckBox,  # Add this import
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QKeyEvent, QTextCursor  # Add this import
from interface.ai.openai_client import OpenAIClient
from interface.ai.controller_agent import ControllerAgent  # Add this import
from interface.constants import settings

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from interface.file_explorer_ui import FileExplorerUI


class AIResponseThread(QThread):
    response_ready = Signal(str)

    def __init__(self, messages):
        super().__init__()
        self.openai_client = OpenAIClient(
            settings.value("api_key", ""),
            settings.value("custom_url", "https://api.openai.com/v1"),
        )
        self.messages = messages

    def run(self):
        response = self.openai_client.chat_completion(self.messages)
        ai_message = response["choices"][0]["message"]["content"]
        self.response_ready.emit(ai_message)


class ChatWindow(QWidget):
    def __init__(self, parent: "FileExplorerUI"):
        super().__init__()
        self.parent: "FileExplorerUI" = parent
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
        self.user_input.installEventFilter(self)  # Install event filter
        layout.addWidget(self.user_input)

        # Send button
        button_layout = QHBoxLayout()

        # Add the "Allow AI control" checkbox
        self.ai_control_checkbox = QCheckBox("Allow AI control")
        button_layout.addWidget(self.ai_control_checkbox)

        button_layout.addStretch()
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        button_layout.addWidget(self.send_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.messages = []

        self.controller_agent = ControllerAgent(self)  # Add this line

    def send_message(self):
        user_message = self.user_input.toPlainText().strip()
        if user_message:
            self.messages.append({"role": "user", "content": user_message})
            self.chat_history.append(f"You: {user_message}")
            self.user_input.clear()

            if self.ai_control_checkbox.isChecked():
                self.handle_controller_agent(user_message)
            else:
                self.response_thread = AIResponseThread(self.messages)
                self.response_thread.response_ready.connect(self.handle_ai_response)
                self.response_thread.start()

    def handle_controller_agent(self, user_message):
        response = self.controller_agent.process_query(user_message, self.messages)
        self.handle_ai_response(response)

    def handle_ai_response(self, ai_message):
        self.chat_history.append(f"AI: {ai_message}")
        self.messages.append({"role": "assistant", "content": ai_message})

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

    def eventFilter(self, obj, event):
        if obj == self.user_input and isinstance(event, QKeyEvent):
            if (
                event.type() == QKeyEvent.KeyPress
                and event.modifiers() == Qt.ControlModifier
                and event.key() == Qt.Key_Return
            ):
                self.send_message()
                return True
        return super().eventFilter(obj, event)

    def set_current_directory(self, folder_path: str):
        return self.parent.change_directory(folder_path)

    def go_up(self):
        return self.parent.go_up()

    def go_back(self):
        return self.parent.go_back()

    def go_forward(self):
        return self.parent.go_forward()

    def get_favorite_directories(self):
        if self.parent and hasattr(self.parent, "favorites_manager"):
            return self.parent.get_favorite_directories()
        return []

    def get_current_directory(self):
        return self.parent.get_current_directory()
