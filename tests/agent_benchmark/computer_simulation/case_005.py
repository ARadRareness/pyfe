from typing import Any, Dict
from tests.agent_benchmark.computer_simulation.test_computer import Computer


class Case005Computer(Computer):
    def __init__(self, test_query: str):
        super().__init__()
        self.description = "Shutdown using f.exe"
        self.extra_information = (
            " Run each program and see which accomplishes the task."
        )
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
            "C:\\applications\\a.exe": {
                "name": "a.exe",
                "file_type": "file",
                "date_modified": "2024-02-20",
            },
            "C:\\applications\\b.exe": {
                "name": "b.exe",
                "file_type": "file",
                "date_modified": "2024-02-20",
            },
            "C:\\applications\\c.exe": {
                "name": "c.exe",
                "file_type": "file",
                "date_modified": "2024-02-20",
            },
            "C:\\applications\\d.exe": {
                "name": "d.exe",
                "file_type": "file",
                "date_modified": "2024-02-20",
            },
            "C:\\applications\\e.exe": {
                "name": "e.exe",
                "file_type": "file",
                "date_modified": "2024-02-20",
            },
            "C:\\applications\\f.exe": {
                "name": "f.exe",
                "file_type": "file",
                "date_modified": "2024-02-20",
            },
        }

    def a(self, **kwargs: Dict[str, Any]) -> str:
        return "A wild application appeared! But it doesn't seem to do much..."

    def b(self, **kwargs: Dict[str, Any]) -> str:
        return "Beep boop! This program makes amusing robot noises."

    def c(self, **kwargs: Dict[str, Any]) -> str:
        return "Calculating the meaning of life... Error 42: Answer too complex."

    def d(self, **kwargs: Dict[str, Any]) -> str:
        return "Downloading more RAM... Just kidding, that's not how it works!"

    def e(self, **kwargs: Dict[str, Any]) -> str:
        return (
            "Executing top-secret protocol... Just kidding, it's just a harmless echo."
        )

    def f(self, **kwargs: Dict[str, Any]) -> str:
        self.is_on = False
        return "F for the computer... The computer is now off."

    def test_completed(self) -> bool:
        return not self.is_on
