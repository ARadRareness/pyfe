import os
from PySide6.QtCore import QObject, QDir, Signal, QDateTime


class NavigationManager(QObject):
    path_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.history_backward: list[str] = []
        self.history_forward: list[str] = []
        self.current_path = os.path.normpath(QDir.rootPath())
        self.history = [(self.current_path, QDateTime.currentDateTime())]

    def get_current_path(self) -> str:
        return self.current_path

    def navigate_to(self, path: str):
        if path != self.current_path:
            self.history_backward.append(self.current_path)
            self.history_forward.clear()
            self.current_path = path
            self.history.append((path, QDateTime.currentDateTime()))
            self.path_changed.emit(self.current_path)
            return True
        return False

    def go_back(self):
        if self.history_backward:
            self.history_forward.append(self.current_path)
            self.current_path = self.history_backward.pop()
            self.path_changed.emit(self.current_path)
            return True
        return False

    def go_forward(self):
        if self.history_forward:
            self.history_backward.append(self.current_path)
            self.current_path = self.history_forward.pop()
            self.path_changed.emit(self.current_path)
            return True
        return False

    def go_up(self):
        parent_path = os.path.normpath(QDir(self.current_path).filePath(".."))
        if parent_path != self.current_path:
            self.navigate_to(parent_path)
            return True
        return False

    def can_go_back(self) -> bool:
        return bool(self.history_backward)

    def can_go_forward(self) -> bool:
        return bool(self.history_forward)

    def can_go_up(self):
        # Handle Windows root paths (e.g., C:\, D:\)
        if os.name == "nt" and self.current_path.endswith(":\\"):
            return False

        # Handle Unix-like root path
        if self.current_path == "/":
            return False

        # For all other cases, check if the parent is different from the current path
        parent_path = os.path.dirname(self.current_path)
        return parent_path != self.current_path

    def handle_backspace(self):
        if self.can_go_back():
            self.go_back()
            return True
        return False

    def get_history(self):
        return list(reversed(self.history))
