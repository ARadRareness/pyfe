import os
from typing import Dict, List
import unittest
from interface.ai.controller_agent_react import ControllerAgent

# HOW TO RUN TESTS:
# python -m unittest tests.test_controller_agent


class TestControllerAgent(unittest.TestCase):
    def setUp(self):
        self.computer = Computer()
        self.controller_agent = ControllerAgent(self.computer)

    def test_find_and_open_folder_auto(self):
        self._run_agent(
            "Can you find and open the woop folder for me?",
        )
        self.assertLessEqual(self.controller_agent.total_actions, 5)
        self.assertEqual(self.computer.get_current_directory(), "C:\\woop")

    def test_go_up(self):
        self.computer.change_directory("C:\\woop\\bla")
        self._run_agent("Can you go up one directory?")
        self.assertEqual(self.computer.get_current_directory(), "C:\\woop")
        self.assertLessEqual(self.controller_agent.total_actions, 5)

    def test_list_directory(self):
        self.computer.change_directory("C:\\")
        self._run_agent("Go to the directory starting with 'he'?")
        self.assertEqual(self.computer.get_current_directory(), "C:\\hello")
        self.assertLessEqual(self.controller_agent.total_actions, 5)

    def test_list_directory2(self):
        self.computer.change_directory("C:\\")
        self._run_agent(
            "Go to the hello folder and confirm that there is a file called 'world.txt'"
        )
        self.assertEqual(self.computer.get_current_directory(), "C:\\hello")
        self.assertLessEqual(self.controller_agent.total_actions, 7)

    def test_go_back(self):  # This test is failing because the agent does weird stuff
        self.computer.change_directory("C:\\woop")
        self.computer.change_directory("C:\\woop\\bla")
        self._run_agent("Can you go back a directory?")
        self.assertEqual(self.computer.get_current_directory(), "C:\\woop")

    def _run_agent(self, query: str):
        self.controller_agent.process_query(query, [])
        print(f"Agent ran for {self.controller_agent.total_actions} steps")


class Computer:
    def __init__(self):
        self.current_directory = "C:\\"

        self.history_backward: list[str] = []
        self.history_forward: list[str] = []

        self.files = {
            "C:\\": {
                "name": "C:",
                "date_modified": "2024-02-20",
                "file_type": "folder",
            },
            "C:\\hello": {
                "name": "hello",
                "date_modified": "2024-02-20",
                "file_type": "folder",
            },
            "C:\\hello\\world.txt": {
                "name": "world.txt",
                "date_modified": "2024-02-20",
                "file_type": "file",
            },
            "C:\\woop": {
                "name": "woop",
                "date_modified": "2024-02-20",
                "file_type": "folder",
            },
            "C:\\woop\\bla": {
                "name": "bla",
                "date_modified": "2024-02-20",
                "file_type": "folder",
            },
        }

    def reset_computer(self):
        self.current_directory = "C:\\"

    def change_directory(self, directory: str):
        if directory not in self.files:
            return False

        if self.files[directory]["file_type"] != "folder":
            return False

        if directory != self.current_directory:
            self.history_backward.append(self.current_directory)
            self.history_forward.clear()
            self.current_directory = directory
        return True

    def get_current_directory(self):
        return self.current_directory

    def list_directory(self):
        current_dir = self.current_directory
        contents = []
        for path, info in self.files.items():
            if os.path.dirname(path) == current_dir and path != current_dir:
                contents.append(info["name"])
        return contents

    def go_up(self):
        parent_directory = os.path.dirname(self.current_directory)

        if parent_directory in self.files:
            self.current_directory = parent_directory
            return True

        return False

    def go_back(self):
        if self.history_backward:
            self.history_forward.append(self.current_directory)
            self.current_directory = self.history_backward.pop()
            return True
        return False

    def go_forward(self):
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


if __name__ == "__main__":
    unittest.main()
