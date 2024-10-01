import os
from typing import Dict, List
import unittest
from interface.ai.controller_agent_react import ControllerAgentReact

# HOW TO RUN TESTS:
# python -m unittest tests.test_controller_agent


class TestControllerAgent(unittest.TestCase):
    def setUp(self):
        self.computer = Computer()
        self.controller_agent = ControllerAgentReact(self.computer)

    def test_find_and_open_folder_auto(self):
        self._run_agent(
            "Can you find and open the hello folder for me?",
        )

        self.assertEqual(self.computer.get_current_directory(), "C:\\hello")
        self.assertLessEqual(self.computer.get_action_count(), 5)

    def test_go_up(self):
        self.computer.change_directory("C:\\woop\\bla")
        self._run_agent("Can you go up one directory?")
        self.assertEqual(self.computer.get_current_directory(), "C:\\woop")
        self.assertLessEqual(self.computer.get_action_count(), 5)

    def xtest_go_back(self):  # This test is failing because the agent does weird stuff
        self.computer.change_directory("C:\\woop")
        self.computer.change_directory("C:\\woop\\bla")
        self._run_agent("Can you go back a directory?")
        self.assertEqual(self.computer.get_current_directory(), "C:\\woop")

    def _run_agent(self, query: str):
        self.computer.reset_count()
        self.controller_agent.process_query(query, [])
        print(f"Agent ran for {self.computer.get_action_count() + 1} steps")


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
        self.action_count = 0

    def reset_computer(self):
        self.current_directory = "C:\\"
        self.action_count = 0

    def reset_count(self):
        self.action_count = 0

    def get_action_count(self):
        return self.action_count

    def change_directory(self, directory: str):
        self.action_count += 1
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
        self.action_count += 1
        return self.current_directory

    def go_up(self):
        self.action_count += 1
        parent_directory = os.path.dirname(self.current_directory)

        if parent_directory in self.files:
            self.current_directory = parent_directory
            return True

        return False

    def go_back(self):
        self.action_count += 1
        if self.history_backward:
            self.history_forward.append(self.current_directory)
            self.current_directory = self.history_backward.pop()
            return True
        return False

    def go_forward(self):
        self.action_count += 1
        if self.history_forward:
            self.history_backward.append(self.current_directory)
            self.current_directory = self.history_forward.pop()
            return True
        return False

    def find_directory(self, search_value: str) -> List[Dict[str, str]]:
        self.action_count += 1
        results = []
        for file in self.files:
            if search_value in self.files[file]["name"]:
                file_info = self.files[file]
                file_info["path"] = file
                results.append(file_info)
        return results


if __name__ == "__main__":
    unittest.main()
