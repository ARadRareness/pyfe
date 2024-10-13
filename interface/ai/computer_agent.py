from typing import List, Dict, Tuple


class ComputerAgent:
    def __init__(self, computer_interface):
        self.computer_interface = computer_interface
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
            "list_directory": "Current directory: {current_directory}\nContents of the current directory:\n{directory_contents}",
            "run_application_success": "Output: {output}",
            "run_application_failure": "Failed to run the application '{app_name}'. Reason: {reason}",
        }
        self.domain_specific_prompt = ""

    def get_examples(self) -> str:
        return """
### Example 1: Navigate to "hello" folder

Task: Go to the folder "hello"
Thought 1: In order to go to the image folder, I need to first check if it exists in the current directory.
Action 1: list_directory
Observation 1: Current directory: C:\\current_user, Contents of the current directory:
- image
- documents
- downloads
Thought 2: The folder "hello" is not in the current directory, I therefore need to search for it, and then change the current directory to it.
Action 2: find_directory § hello
Observation 2: Found 1 directories containing 'hello':
- hello (Path: C:\\hello, Modified: 2024-02-20)
Thought 3: I have found the folder "hello", now I need to change the current directory to it.
Action 3: change_directory § C:\\hello
Observation 3: Successfully changed the current directory to "C:\\hello"
Thought 4: I have successfully reached the folder "hello", I can now report this to the user.
Action 4: answer § I have changed the current directory to the folder "hello"

### Example 2: Navigate Up Directory

Task: Go up one directory
Thought 1: In order to go up one directory, I need to use the go_up function.
Action 1: go_up
Observation 1: Successfully moved up one directory level, current directory: C:\\.
Thought 2: I have successfully gone up one directory level, I can now report this to the user.
Action 2: answer § I have gone up one directory to C:\\.

### Example 3: Navigate to Image Folder

Task: Go to the image folder
Thought 1: In order to go to the image folder, I need to first check if it exists in the current directory.
Action 1: list_directory
Observation 1: Current directory: C:\\, Contents of the current directory:
- image
- documents
- downloads
Thought 2: The image folder exists in the current directory, I can now change to it.
Action 2: change_directory § C:\\image
Observation 2: Successfully changed the current directory to "C:\\image"
Thought 3: I have successfully reached the folder "image", I can now report this to the user.
Action 3: answer § I have changed the current directory to the folder "C:\\image"
"""

    def get_available_functions(self) -> str:
        return """
1. find_directory(search_value: str)
   - Searches globally for directories containing the given search value

2. change_directory(folder_path: str)
   - Changes current directory to specified folder path
   - Returns new directory path if successful

3. go_up
   - Moves up one directory level
   - Returns new directory path if successful

4. go_back
   - Moves to previously visited directory in navigation history

5. go_forward
   - Moves to next directory in navigation history, if available

6. current_directory
   - Gets current directory path

7. list_directory
   - Lists all files and folders in current directory
   - Takes no arguments

8. run_application(application_path: str, **kwargs)
   - Runs specified application with optional keyword arguments

9. answer(response: str)
   - Provides final answer to user's task"""

    def get_domain_specific_prompt(self) -> str:
        return """You are able to perform various actions on the user's computer.
You can search for directories, change the current directory, go up and down directories,
list the contents of a directory, run applications, and provide a final answer to the user's task.
"""

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
        elif function == "list_directory":
            return self.list_directory(), False
        elif function == "run_application":
            return self.run_application(argument), False
        else:
            print(f"Warning: Unknown action ({function}) was provided.")
            return f"Unknown action: {function}", False

    def find_directory(self, search_value: str) -> str:
        if not search_value:
            return "No search value provided"

        results: List[Dict[str, str]] = self.computer_interface.find_directory(
            search_value
        )

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

    def change_directory(self, folder_path: str) -> str:
        if not folder_path:
            return self.action_responses["change_directory_no_argument"]

        if self.computer_interface.change_directory(folder_path):
            return self.action_responses["change_directory_success"].format(
                folder_path=folder_path
            )
        else:
            return self.action_responses["change_directory_incorrect_path"]

    def go_up(self) -> str:
        if self.computer_interface.go_up():
            return self.action_responses["go_up_success"]
        else:
            return self.action_responses["go_up_failure"]

    def go_back(self) -> str:
        if self.computer_interface.go_back():
            return self.action_responses["go_back_success"]
        else:
            return self.action_responses["go_back_failure"]

    def go_forward(self) -> str:
        if self.computer_interface.go_forward():
            return self.action_responses["go_forward_success"]
        else:
            return self.action_responses["go_forward_failure"]

    def current_directory(self) -> str:
        current_directory: str = self.computer_interface.get_current_directory()
        return self.action_responses["current_directory"].format(
            directory_path=current_directory
        )

    def list_directory(self) -> str:
        current_dir = self.computer_interface.get_current_directory()
        contents = self.computer_interface.list_directory()

        if not contents:
            return self.action_responses["list_directory"].format(
                current_directory=current_dir,
                directory_contents="The current directory is empty.",
            )

        directory_contents = "\n".join(f"- {item}" for item in contents)
        return self.action_responses["list_directory"].format(
            current_directory=current_dir, directory_contents=directory_contents
        )

    def run_application(self, arguments: str) -> str:
        kwargs: Dict[str, str] = {}

        if arguments.startswith('"'):
            # Find the closing quote for the application path
            path_end = arguments.find('"', 1)
            if path_end == -1:
                return self.action_responses["run_application_failure"].format(
                    app_name="", reason="Invalid application path format"
                )
            application_path = arguments[1:path_end]
            remaining_args = arguments[path_end + 1 :].strip()
        else:
            # Find the first space to separate application path from arguments
            space_index = arguments.find(" ")
            if space_index == -1:
                application_path = arguments
                remaining_args = ""
            else:
                application_path = arguments[:space_index]
                remaining_args = arguments[space_index + 1 :].strip()

        if remaining_args:
            kwargs["arguments"] = remaining_args

        result = self.computer_interface.run_application(application_path, **kwargs)

        if (
            isinstance(result, str)
            and result.startswith("Computer is off")
            or result.endswith("is not a valid program.")
        ):
            return self.action_responses["run_application_failure"].format(
                app_name=application_path.split("\\")[-1], reason=result
            )
        else:
            return self.action_responses["run_application_success"].format(
                app_name=application_path.split("\\")[-1], output=result
            )
