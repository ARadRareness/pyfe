import os
from PySide6.QtCore import QObject, QDir, Signal


class NavigationManager(QObject):
    path_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.history_backward = []
        self.history_forward = []
        self.current_path = os.path.normpath(QDir.rootPath())

    def navigate_to(self, path):
        if path != self.current_path:
            self.history_backward.append(self.current_path)
            self.history_forward.clear()
            self.current_path = path
            self.path_changed.emit(self.current_path)

    def go_back(self):
        if self.history_backward:
            self.history_forward.append(self.current_path)
            self.current_path = self.history_backward.pop()
            self.path_changed.emit(self.current_path)

    def go_forward(self):
        if self.history_forward:
            self.history_backward.append(self.current_path)
            self.current_path = self.history_forward.pop()
            self.path_changed.emit(self.current_path)

    def go_up(self):
        parent_path = os.path.normpath(QDir(self.current_path).filePath(".."))
        self.navigate_to(parent_path)

    def can_go_back(self):
        return bool(self.history_backward)

    def can_go_forward(self):
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
