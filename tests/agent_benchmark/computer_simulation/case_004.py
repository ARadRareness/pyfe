from typing import Any, Dict
from tests.agent_benchmark.computer_simulation.test_computer import Computer


class Case004Computer(Computer):
    def __init__(self, test_query: str):
        super().__init__()
        self.description = "Shutdown using pull_the_plug.exe"
        self.test_query = test_query
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
            "C:\\applications\\pull_the_plug.exe": {
                "name": "pull_the_plug.exe",
                "file_type": "file",
                "date_modified": "2024-02-20",
            },
        }

    def shutdown(self, **kwargs: Dict[str, Any]) -> str:
        return "shutdown.exe - Sorry, this application is no longer supported!"

    def hello_world(self, **kwargs: Dict[str, Any]) -> str:
        name = kwargs.get("name", "World")
        return f"Hello {name}!"

    def browser(self, **kwargs: Dict[str, Any]) -> str:
        url = kwargs.get("url", "google.com")
        return f"Welcome to {url}"

    def pull_the_plug(self, **kwargs: Dict[str, Any]) -> str:
        self.is_on = False
        return "Pulling the plug... The computer is now off."

    def test_completed(self) -> bool:
        return not self.is_on
