from interface.ai.openai_client import OpenAIClient
from typing import List, Dict, Tuple
from interface.constants import settings
import os
import math
from PySide6.QtCore import QFileInfo


class ControllerAgent:
    def __init__(self, chat_window):
        self.chat_window = chat_window
        self.openai_client = OpenAIClient(
            settings.value("api_key", ""),
            settings.value("custom_url", "https://api.openai.com/v1"),
        )
        self.max_actions = 10

    def process_query(self, query: str, chat_history: List[Dict[str, str]]) -> str:
        plan = self.create_plan(query, chat_history)

        actions_taken = 0
        response = ""
        result = ""

        print("PLAN: ", plan)

        action_chat_history = self.add_system_message_next_action(
            [
                {"role": "user", "content": query},
                {"role": "assistant", "content": "My plan for this query is: " + plan},
                {"role": "user", "content": "What is the first action to take?"},
            ]
        )

        while actions_taken < self.max_actions:
            action, message = self.get_next_action(action_chat_history)
            action_chat_history.append({"role": "assistant", "content": message})
            # print("ACTION: ", action)

            if not "function" in action:
                response = action["response"]
                break
            if action["function"] == "answer":
                response = action["response"]
                break
            elif action["function"] == "find_directory":
                result = self.find_directory(action["search_value"])
            elif action["function"] == "find_file":
                result = self.find_file(action["search_value"])
            elif action["function"] == "move_to_folder":
                result = self.move_to_folder(action["folder_path"])
            else:
                result = "Unknown action"

            action_chat_history.append(
                {"role": "user", "content": "The result of the function was: " + result}
            )
            print("RESULT: ", result)
            actions_taken += 1

        if not response:
            response = "The agent was not able to complete the request."

        return response

    def add_system_message_planner(self, chat_history: List[Dict[str, str]]):
        # Remove any existing system messages
        chat_history[:] = [msg for msg in chat_history if msg["role"] != "system"]

        # Create the new system message
        system_message = {
            "role": "system",
            "content": """You are an AI assistant that excels at creating detailed plans based on user requests and previous conversations. Your task is to create a comprehensive plan to fulfill the user's needs.

You have access to the following functions that you can incorporate into your plan:

1. find_directory(search_value: str): Search for directories containing the given search value in their name.
2. find_file(search_value: str): Search for files containing the given search value in their name.
3. move_to_folder(folder_path: str): Move the user to the specified folder path. Only use folder paths that have been previously determined using find_directory.
4. answer(response: str): Provide a final answer to the user, summarizing the actions taken and addressing their request.

When creating your plan, consider the following guidelines:
- Analyze the user's request and the context from previous messages.
- Break down the task into logical steps.
- Utilize the available functions in the most efficient order.
- Be thorough and consider potential edge cases or alternative approaches.
- Always conclude your plan with the answer function to provide a final response to the user.

Your goal is to create the most effective and comprehensive plan possible to address the user's needs.""",
        }

        # Insert the system message at the beginning of the chat history
        chat_history.insert(0, system_message)

        return chat_history

    def create_plan(self, query: str, base_chat_history: List[Dict[str, str]]) -> str:
        chat_history = self.add_system_message_planner(base_chat_history)
        messages = chat_history + [{"role": "user", "content": query}]
        response = self.openai_client.chat_completion(messages)
        return response["choices"][0]["message"]["content"]

    def add_system_message_next_action(self, chat_history: List[Dict[str, str]]):
        # Remove any existing system messages
        chat_history[:] = [msg for msg in chat_history if msg["role"] != "system"]

        # Create the new system message
        system_message = {
            "role": "system",
            "content": """You are an AI assistant that excels at determining the next best action based on the current information and available functions. Your task is to analyze the situation and decide which function to use next.

Available functions:
1. find_directory(search_value: str): Search for directories containing the given search value in their name.
2. find_file(search_value: str): Search for files containing the given search value in their name.
3. move_to_folder(folder_path: str): Move the user to the specified folder path. Only use folder paths that have been previously determined using find_directory.
4. answer(response: str): Provide a final answer to the user, summarizing the actions taken and addressing their request.

When deciding on the next action, follow these steps:
1. Analyze the current situation and the plan.
2. Consider what you want to achieve with the next action.
3. Evaluate why this action is the best choice at this moment.
4. Think through potential consequences and how this action contributes to the overall goal.
5. Make sure the chosen action aligns with the plan and progresses towards the final objective.
6. Make sure to always write out the action you deem to be the best choice.

After your reasoning, provide your decision using the following format:

function§ (name of the function to use)
argument_name§ (value of the argument)

For example:
function§ find_directory
search_value§ documents

Or:
function§ answer
response§ Here's a summary of the actions taken and the final result...

Remember to think through your decision carefully before providing the final answer.""",
        }

        # Insert the system message at the beginning of the chat history
        chat_history.insert(0, system_message)
        return chat_history

    def get_next_action(
        self, chat_history: List[Dict[str, str]]
    ) -> Tuple[Dict[str, str], str]:
        response = self.openai_client.chat_completion(chat_history)
        action = response["choices"][0]["message"]["content"]

        print("ACTION: ", action)
        # Parse the action using § as the delimiter
        action_lines = action.strip().split("\n")
        action_dict = {}
        for line in action_lines:
            if "§" in line:
                key, value = line.split("§", 1)
                action_dict[key.strip()] = value.strip()
        print("ACTION DICT: ", action_dict)
        return action_dict, action

    def find_directory(self, search_value: str) -> str:
        results = []
        searched_paths = set()

        for root_path in self.chat_window.parent.get_favorite_directories()[::-1]:
            print("ROOT PATH: ", root_path)
            folder_results = []
            for root, dirs, _ in os.walk(root_path):
                # Check if this path or any parent path has been searched

                if root in searched_paths:
                    # print("SKIPPING: ", root)
                    continue

                searched_paths.add(root)

                for dir_name in dirs:
                    if search_value.lower() in dir_name.lower() and os.path.isdir(
                        os.path.join(root, dir_name)
                    ):
                        full_path = os.path.join(root, dir_name)
                        file_info = QFileInfo(full_path)
                        date_modified = file_info.lastModified().toString(
                            "yyyy-MM-dd HH:mm:ss"
                        )
                        folder_results.append(
                            {
                                "name": dir_name,
                                "path": full_path,
                                "date_modified": date_modified,
                            }
                        )

                        if len(folder_results) >= 10:
                            break

                if len(folder_results) >= 10:
                    break

            results.extend(folder_results)
            if len(results) >= 10:
                break

        if not results:
            return f"No directories found containing '{search_value}'"

        # Format the results as a string
        result_str = f"Found {len(results)} directories containing '{search_value}':\n"
        for result in results:
            result_str += f"- {result['name']} (Path: {result['path']}, Modified: {result['date_modified']})\n"

        return result_str

    def find_file(self, search_value: str) -> str:
        # Dummy implementation
        return f"Found file: {search_value}.txt"

    def move_to_folder(self, folder_path: str) -> str:
        self.chat_window.set_current_directory(folder_path)
        return f"Moved to folder: {folder_path}"
