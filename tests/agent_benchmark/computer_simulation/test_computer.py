import os
from typing import Dict, List, Any


class Computer:
    def __init__(self):
        self.is_on = True
        self.current_directory = "C:\\"
        self.history_backward: list[str] = []
        self.history_forward: list[str] = []
        self.files: Dict[str, Dict[str, str]] = {}

    def run_application(self, application_path: str, **kwargs: Any) -> str:
        if not self.is_on:
            return "Computer is off."

        # Check if the application exists in the current directory
        full_path = self.current_directory.rstrip("\\") + "\\" + application_path

        if (
            application_path not in self.files
            and full_path not in self.files
            or (
                application_path in self.files
                and self.files[application_path]["file_type"] != "file"
            )
            or (
                full_path in self.files and self.files[full_path]["file_type"] != "file"
            )
        ):
            return f"{application_path} is not a valid program."

        # Use the full path if it exists, otherwise use the original application_path
        app_path = full_path if full_path in self.files else application_path
        app_name = app_path.split("\\")[-1].split(".")[0]
        return getattr(self, app_name)(**kwargs)

    def change_directory(self, directory: str) -> bool:
        if directory not in self.files:
            return False

        if self.files[directory]["file_type"] != "folder":
            return False

        if directory != self.current_directory:
            self.history_backward.append(self.current_directory)
            self.history_forward.clear()
            self.current_directory = directory
        return True

    def get_current_directory(self) -> str:
        return self.current_directory

    def list_directory(self, path: str = "") -> List[str]:
        target_dir = path if path else self.current_directory
        if (
            target_dir not in self.files
            or self.files[target_dir]["file_type"] != "folder"
        ):
            return []

        contents = []
        for file_path, info in self.files.items():
            if os.path.dirname(file_path) == target_dir and file_path != target_dir:
                contents.append(info["name"])
        return contents

    def go_up(self) -> bool:
        parent_directory = os.path.dirname(self.current_directory)
        if parent_directory in self.files:
            self.current_directory = parent_directory
            return True
        return False

    def go_back(self) -> bool:
        if self.history_backward:
            self.history_forward.append(self.current_directory)
            self.current_directory = self.history_backward.pop()
            return True
        return False

    def go_forward(self) -> bool:
        if self.history_forward:
            self.history_backward.append(self.current_directory)
            self.current_directory = self.history_forward.pop()
            return True
        return False

    def find_directory(self, search_value: str) -> List[Dict[str, str]]:
        results = []
        for file, info in self.files.items():
            if search_value in info["name"] and info["file_type"] == "folder":
                file_info = info.copy()
                file_info["path"] = file
                results.append(file_info)
        return results

    def reset_computer(self):
        self.is_on = True
        self.current_directory = "C:\\"
        self.history_backward.clear()
        self.history_forward.clear()
