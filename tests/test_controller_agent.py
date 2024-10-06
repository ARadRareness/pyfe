import unittest
from interface.ai.controller_agent_react import ControllerAgent
from interface.ai.computer_agent import ComputerAgent
from tests.agent_benchmark.computer_simulation.test_computer import Computer

# HOW TO RUN TESTS:
# python -m unittest tests.test_controller_agent


class TestControllerAgent(unittest.TestCase):
    def setUp(self):
        self.computer = Computer()
        self.computer.files = {
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
        self.computer_agent = ComputerAgent(self.computer)
        self.controller_agent = ControllerAgent(self.computer_agent)

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

    def test_go_back(self):
        self.computer.change_directory("C:\\woop")
        self.computer.change_directory("C:\\woop\\bla")
        self._run_agent("Can you go back a directory?")
        self.assertEqual(self.computer.get_current_directory(), "C:\\woop")

    def _run_agent(self, query: str):
        self.controller_agent.process_query(query, [])
        print(f"Agent ran for {self.controller_agent.total_actions} steps")


if __name__ == "__main__":
    unittest.main()
