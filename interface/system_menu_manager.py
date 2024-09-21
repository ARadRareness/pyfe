from PySide6.QtWidgets import QMenuBar, QMenu
from PySide6.QtCore import QSettings
from PySide6.QtGui import QAction


class SystemMenuManager:
    def __init__(self, parent):
        self.parent = parent
        self.settings = QSettings("ARadRareness", "PythonFileExplorer")
        self.create_system_menu()

    def create_system_menu(self):
        menu_bar = QMenuBar(self.parent)
        self.parent.setMenuBar(menu_bar)

        # Create Options menu
        options_menu = QMenu("Options", self.parent)
        menu_bar.addMenu(options_menu)

        # Create Enable AI action
        self.enable_ai_action = QAction("Enable AI", self.parent, checkable=True)
        self.enable_ai_action.setChecked(
            self.settings.value("enable_ai", False, type=bool)
        )
        self.enable_ai_action.triggered.connect(self.toggle_ai)
        options_menu.addAction(self.enable_ai_action)

    def toggle_ai(self):
        is_enabled = self.enable_ai_action.isChecked()
        self.settings.setValue("enable_ai", is_enabled)
        print(f"AI is now {'enabled' if is_enabled else 'disabled'}")
        # Add any additional logic for enabling/disabling AI features
