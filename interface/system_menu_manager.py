from PySide6.QtWidgets import QMenuBar, QMenu, QMessageBox
from PySide6.QtCore import QSettings
from PySide6.QtGui import QAction
from interface.ai.openai_utils import OpenAIUtils


class SystemMenuManager:
    def __init__(self, parent):
        self.parent = parent
        self.settings = QSettings("ARadRareness", "PythonFileExplorer")
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
            self.settings.value("enable_ai", False, type=bool)
        )

        # Create Options menu
        options_menu = QMenu("Options", self.parent)
        menu_bar.addMenu(options_menu)

        # Create Enable AI action
        self.enable_ai_action = QAction("Enable AI", self.parent, checkable=True)
        self.enable_ai_action.setChecked(
            self.settings.value("enable_ai", False, type=bool)
            and OpenAIUtils.is_available()
        )
        self.enable_ai_action.triggered.connect(self.toggle_ai)
        options_menu.addAction(self.enable_ai_action)

    def toggle_ai(self):
        if not OpenAIUtils.is_available() and self.enable_ai_action.isChecked():
            OpenAIUtils.show_not_available(self.parent)
            self.enable_ai_action.setChecked(False)
            return

        is_enabled = self.enable_ai_action.isChecked()
        self.settings.setValue("enable_ai", is_enabled)
        print(f"AI is now {'enabled' if is_enabled else 'disabled'}")
        self.generate_image_action.setVisible(is_enabled)

    def show_generate_image_dialog(self):
        self.parent.image_generator.show_generate_image_dialog(
            self.parent, self.parent.current_path
        )
