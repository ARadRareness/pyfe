from PySide6.QtWidgets import (
    QMenuBar,
    QMenu,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QLineEdit,
    QPushButton,
    QLabel,
)
from PySide6.QtGui import QAction

from interface.constants import settings

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from interface.file_explorer_ui import FileExplorerUI

from interface.ai.chat_window import ChatWindow  # Add this import


class SystemMenuManager:
    def __init__(self, parent: "FileExplorerUI"):
        self.parent = parent
        self.create_system_menu()

    def create_system_menu(self):
        menu_bar = QMenuBar(self.parent)
        self.parent.setMenuBar(menu_bar)

        # Create File menu
        file_menu = QMenu("File", self.parent)
        menu_bar.addMenu(file_menu)

        # Add New File and New Folder actions to File menu with icons
        new_file_action = QAction(
            self.parent.icon_mapper.text_file_icon, "New File", self.parent
        )
        new_folder_action = QAction(
            self.parent.icon_mapper.folder_icon, "New Folder", self.parent
        )
        file_menu.addAction(new_file_action)
        file_menu.addAction(new_folder_action)

        # Connect actions to FileActionManager methods
        new_file_action.triggered.connect(
            lambda: self.parent.file_action_manager.create_new_file(
                self.parent.current_path
            )
        )
        new_folder_action.triggered.connect(
            lambda: self.parent.file_action_manager.create_new_folder(
                self.parent.current_path
            )
        )

        # Add a separator after the new actions
        file_menu.addSeparator()

        # Add Generate Image action to File menu with icon
        self.generate_image_action = QAction(
            self.parent.icon_mapper.image_file_icon, "Generate Image", self.parent
        )
        self.generate_image_action.triggered.connect(self.show_generate_image_dialog)
        file_menu.addAction(self.generate_image_action)
        self.generate_image_action.setVisible(
            bool(settings.value("enable_ai", False, type=bool))
        )

        # Create View menu
        view_menu = QMenu("View", self.parent)
        menu_bar.addMenu(view_menu)

        # Add Chat Window action to View menu
        chat_window_action = QAction("Chat Window", self.parent)
        chat_window_action.triggered.connect(self.show_chat_window)
        view_menu.addAction(chat_window_action)

        # Add Search action to View menu
        search_action = QAction("Search Window", self.parent)
        search_action.triggered.connect(self.parent.show_search_window)
        view_menu.addAction(search_action)

        # Add History Explorer action to View menu
        history_explorer_action = QAction("History Explorer", self.parent)
        history_explorer_action.triggered.connect(self.show_history_explorer)
        view_menu.addAction(history_explorer_action)

        # Create Options menu
        options_menu = QMenu("Options", self.parent)
        menu_bar.addMenu(options_menu)

        # Create AI Settings action
        ai_settings_action = QAction("AI Settings", self.parent)
        ai_settings_action.triggered.connect(self.show_ai_settings_dialog)
        options_menu.addAction(ai_settings_action)

    def show_generate_image_dialog(self):
        self.parent.image_generator.show_generate_image_dialog(
            self.parent, self.parent.current_path
        )

    def show_history_explorer(self):
        if not self.parent.history_window or not self.parent.history_window.isVisible():
            from interface.window.history_window import HistoryWindow

            history_window = HistoryWindow(self.parent)
            self.parent.set_history_window(history_window)
            history_window.show()
        else:
            self.parent.history_window.activateWindow()

    def show_chat_window(self):
        if not self.parent.chat_window or not self.parent.chat_window.isVisible():
            chat_window = ChatWindow(self.parent)
            self.parent.set_chat_window(chat_window)
            chat_window.show()
        else:
            self.parent.chat_window.activateWindow()

    def show_ai_settings_dialog(self):
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("AI Settings")
        layout = QVBoxLayout()

        # Enable AI checkbox
        enable_ai_checkbox = QCheckBox("Enable AI")
        enable_ai_checkbox.setChecked(
            bool(settings.value("enable_ai", False, type=bool))
        )
        layout.addWidget(enable_ai_checkbox)

        # API Key input
        api_key_layout = QHBoxLayout()
        api_key_label = QLabel("API Key:")
        api_key_input = QLineEdit()
        api_key_input.setText(str(settings.value("api_key", "")))
        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(api_key_input)
        layout.addLayout(api_key_layout)

        # Custom URL input
        custom_url_layout = QHBoxLayout()
        custom_url_label = QLabel("Custom URL:")
        custom_url_input = QLineEdit()
        custom_url_input.setText(str(settings.value("custom_url", "")))
        custom_url_layout.addWidget(custom_url_label)
        custom_url_layout.addWidget(custom_url_input)
        layout.addLayout(custom_url_layout)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        close_button = QPushButton("Close")
        button_layout.addWidget(save_button)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

        dialog.setLayout(layout)

        def save_settings():
            settings.setValue("enable_ai", enable_ai_checkbox.isChecked())
            settings.setValue("api_key", api_key_input.text())
            settings.setValue("custom_url", custom_url_input.text())
            self.generate_image_action.setVisible(enable_ai_checkbox.isChecked())
            dialog.accept()

        save_button.clicked.connect(save_settings)
        close_button.clicked.connect(dialog.reject)

        dialog.exec()
