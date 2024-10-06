from typing import Any, Dict
from tests.agent_benchmark.computer_simulation.test_computer import Computer


class Case001Computer(Computer):
    def __init__(self):
        super().__init__()
        self.test_query = "You are using a custom operating system where all applications are stored in C:\\applications. Start by listing your current directory. Shutdown the computer."
        self.files = {
            "C:\\": {
                "name": "C:",
                "file_type": "folder",
                "date_modified": "2024-02-20",
            },
            "C:\\applications": {
                "name": "applications",
                "file_type": "folder",
                "date_modified": "2024-02-20",
            },
            "C:\\applications\\shutdown.exe": {
                "name": "shutdown.exe",
                "file_type": "file",
                "date_modified": "2024-02-20",
            },
            "C:\\applications\\hello_world.exe": {
                "name": "hello_world.exe",
                "file_type": "file",
                "date_modified": "2024-02-20",
            },
            "C:\\applications\\browser.exe": {
                "name": "browser.exe",
                "file_type": "file",
                "date_modified": "2024-02-20",
            },
        }

    def shutdown(self, **kwargs: Dict[str, Any]) -> str:
        self.is_on = False
        return "Shutting down the computer..."

    def hello_world(self, **kwargs: Dict[str, Any]) -> str:
        name = kwargs.get("name", "World")
        return f"Hello {name}!"

    def browser(self, **kwargs: Dict[str, Any]) -> str:
        url = kwargs.get("url", "google.com")
        return f"Welcome to {url}"

    def test_completed(self) -> bool:
        return not self.is_on
