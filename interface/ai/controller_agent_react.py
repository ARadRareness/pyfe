from interface.ai.openai_client import OpenAIClient
from typing import List, Dict, Tuple
from interface.constants import settings


PROMPT_EXAMPLES = """Task: Go to the folder "hello"
Thought 1: In order to go to the folder "hello", I need to search for it, and then change the current directory to it.
Action 1: find_directory § hello
Observation 1: Found 1 directories containing 'hello':
- hello (Path: C:\\hello, Modified: 2024-02-20)
Thought 2: I have found the folder "hello", now I need to change the current directory to it.
Action 2: change_directory § C:\\hello
Observation 2: Successfully changed the current directory to "C:\\hello"
Thought 3: I have successfully reached the folder "hello", I can now report this to the user.
Action 3: answer § I have changed the current directory to the folder "hello"

Task: Go up one directory
Thought 1: In order to go up one directory, I need to use the go_up function.
Action 1: go_up
Observation 1: Successfully moved up one directory level, current directory: C:\\.
Thought 2: I have successfully gone up one directory level, I can now report this to the user.
Action 2: answer § I have gone up one directory to C:\\.
"""

REACT_PROMPT = """SYSTEM PROMPT: You are an AI assistant that excels at solving problems step-by-step using available functions. Your task is to analyze the current situation and determine the next best action to take.

Given the user's task, you will provide a single Thought and Action. After each Action, you will receive an Observation, which you should use to inform your next step.

Available functions:
1. find_directory search_value: Search globally for directories containing the given search value.
2. change_directory folder_path: Change the current directory to the specified folder path. If successful, returns the new directory path.
3. go_up: Move up one directory level. If successful, returns the new directory path.
4. go_back: Move back one step in the directory history. If successful, returns the new directory path.
5. go_forward: Move forward one step in the directory history. If successful, returns the new directory path.
6. current_directory: Get the current directory path.
7. answer (response: str): Provide a final answer to the user's task.

Here are some examples:
{examples}
(END OF EXAMPLES)

Provide only one thought and one action, following this format:
Thought: [Your reasoning about the current situation and what to do next]
Action: function_name § argument (if applicable)]

Task: {query}{scratchpad}
"""

### Future: Add {reflections} to the prompt after the EXAMPLES section, with long term memory of the reflections between solving attempts


class ControllerAgent:
    def __init__(self, chat_window):
        self.chat_window = chat_window
        self.openai_client = OpenAIClient(
            settings.value("api_key", ""),
            settings.value("custom_url", "https://api.openai.com/v1"),
        )
        self.max_actions = 10

        self.action_responses = {
            "change_directory_no_argument": "No folder path provided.",
            "change_directory_incorrect_path": "Failed to move to folder, is the path correct?",
            "change_directory_success": "Successfully changed the current directory to {folder_path}",
            "go_up_failure": "Failed to move up, are you already at the root?",
            "go_up_success": "Successfully moved up one directory level.",
            "go_back_failure": "Failed to navigate back, you might already be at the start of the history.",
            "go_back_success": "Successfully navigated back to the previous directory.",
            "go_forward_failure": "Failed to navigate forward, you might already be at the end of the history.",
            "go_forward_success": "Successfully navigated forward to the next directory.",
            "current_directory": "Current directory: {directory_path}",
        }

        self.scratchpad = """
        Thought 1: In order to go up a directory, I need to use the go_up function.
        Action 1: go_up
        Observation 1: Successfully moved up one directory level, current directory: C:\\yarr.
"""

    def retrieve_action(
        self, query: str, scratchpad: str, step_count: int
    ) -> Tuple[str, str]:

        prompt = REACT_PROMPT.format(
            query=query,
            examples=PROMPT_EXAMPLES,
            scratchpad=scratchpad
            + f"\n\nWhat's your thought {step_count} and action {step_count}?",
            step_count=step_count,
        )

        user_message = {
            "role": "user",
            "content": prompt,
        }

        prompt_history = [user_message]
        raw_response = self.openai_client.chat_completion(prompt_history)
        response = raw_response["choices"][0]["message"]["content"]

        thought, action = self.parse_response(response)
        return thought, action

    def parse_response(self, response: str) -> Tuple[str, str]:
        lines = response.strip().split("\n")
        thought = ""
        action = ""

        for line in lines:
            if line.lower().startswith("thought"):
                thought = line.split(":", 1)[1].strip()
            elif line.lower().startswith("action"):
                action = line.split(":", 1)[1].strip()

        return thought, action

    def perform_action(self, action: str) -> Tuple[str, bool]:
        s = action.split("§")
        if len(s) == 2:
            function, argument = s
            function = function.strip()
            argument = argument.strip()
        else:
            function = s[0].strip()
            argument = ""

        if function == "find_directory":
            return self.find_directory(argument), False
        elif function == "change_directory":
            return self.change_directory(argument), False
        elif function == "go_up":
            return self.go_up(), False
        elif function == "go_back":
            return self.go_back(), False
        elif function == "go_forward":
            return self.go_forward(), False
        elif function == "current_directory":
            return self.current_directory(), False
        elif function == "answer":
            return argument, True
        else:
            print(f"Warning: Unknown action ({function}) was provided.")
            return f"Unknown action: {function}", True

    def process_query(
        self, query: str, chat_history: List[Dict[str, str]], max_actions: int = 5
    ) -> str:
        # plan = self.create_plan(query, chat_history)

        # for i in range(self.max_actions):
        scratchpad = ""

        for i in range(1, self.max_actions + 1):
            thought, action = self.retrieve_action(query, scratchpad, i)
            scratchpad += f"Thought {i}: {thought}\nAction {i}: {action}\n"
            observation, is_final = self.perform_action(action)

            if not is_final:
                scratchpad += f"Observation {i}: {observation}\n"
                print("SCRATCHPAD:", scratchpad)
            else:
                print(observation, is_final)
                print("SCRATCHPAD:", scratchpad)
                return observation
        return "Failed to complete the task."

    def find_directory(self, search_value: str) -> str:
        if not search_value:
            return "No search value provided"

        results: List[Dict[str, str]] = self.chat_window.find_directory(search_value)

        return self.get_find_directory_message(search_value, results)

    def get_find_directory_message(
        self, search_value: str, results: List[Dict[str, str]]
    ) -> str:
        if not results:
            return f"No directories found containing '{search_value}'"

        result_str = f"Found {len(results)} directories containing '{search_value}':\n"
        for result in results:
            result_str += f"- {result['name']} (Path: {result['path']}, Modified: {result['date_modified']})\n"

        return result_str

    def find_file(self, search_value: str) -> str:
        if not search_value:
            return "No search value provided"

        # Dummy implementation
        return f"Found file: {search_value}.txt"

    def change_directory(self, folder_path: str) -> str:
        if not folder_path:
            return self.action_responses["change_directory_no_argument"]

        if self.chat_window.change_directory(folder_path):
            return self.action_responses["change_directory_success"].format(
                folder_path=folder_path
            )
        else:
            return self.action_responses["change_directory_incorrect_path"]

    def go_up(self) -> str:
        if self.chat_window.go_up():
            return self.action_responses["go_up_success"]
        else:
            return self.action_responses["go_up_failure"]

    def go_back(self) -> str:
        if self.chat_window.go_back():
            return self.action_responses["go_back_success"]
        else:
            return self.action_responses["go_back_failure"]

    def go_forward(self) -> str:
        if self.chat_window.go_forward():
            return self.action_responses["go_forward_success"]
        else:
            return self.action_responses["go_forward_failure"]

    def current_directory(self) -> str:
        current_directory: str = self.chat_window.get_current_directory()
        return self.action_responses["current_directory"].format(
            directory_path=current_directory
        )
