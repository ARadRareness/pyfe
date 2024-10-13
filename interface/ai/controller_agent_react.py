from interface.ai.openai_client import OpenAIClient
from typing import List, Dict, Tuple
from interface.constants import settings


REACT_PROMPT = """
## Role and Purpose
You are an AI agent specialized in solving problems step-by-step using available functions. Your task is to analyze situations and determine the next best action to take.
{domain_specific_prompt}

## Available Functions
{available_functions}

## Examples
{examples}

## Response Format
Provide only one thought and one action at a time, following this format:
```
Thought: [Your reasoning about the current situation and what to do next]
Action: function_name § argument (if applicable)
```

## Task
{query}{scratchpad}
"""

REACT_ANALYSIS_PROMPT = """
## Role and Purpose
You are an AI agent specialized in comprehensive situation analysis and problem decomposition. Your task is to analyze given scenarios and generate structured reasoning that identifies:
- Key aspects of the current situation
- Relevant constraints and requirements
- Primary goals and sub-goals to achieve
- Potential challenges or obstacles
- Available resources and their applicability
{domain_specific_prompt}

## Available Functions
{available_functions}

## Context
Your analysis will be used by another AI agent to determine specific actions to take. Focus on providing clear, actionable insights rather than suggesting specific functions to call.

## Examples
{examples}

## Response Format
Provide a structured analysis following this format:
```
Situation Analysis:
[Describe the current state and key elements of the scenario]

Goals:
- Primary Goal: [Main objective to achieve]
- Sub-goals:
  1. [First sub-goal]
  2. [Second sub-goal]
  ...

Constraints:
- [List key limitations or requirements]

Available Resources:
- [List relevant resources and their potential uses]

Key Considerations:
- [Important factors that should influence decision-making]
```

## Task
{query}
"""


class ControllerAgent:
    def __init__(self, domain_agent, max_actions: int = 10):
        self.domain_agent = domain_agent
        self.openai_client = OpenAIClient(
            settings.value("api_key", ""),
            settings.value("custom_url", "https://api.openai.com/v1"),
        )
        self.max_actions = max_actions
        self.total_actions = 0
        self.scratchpad = ""
        self.initial_prompt = ""
        # self.use_analysis = True

    def generate_analysis(self, query: str) -> str:
        prompt = REACT_ANALYSIS_PROMPT.format(
            query=query,
            examples=self.domain_agent.get_analysis_examples(),
            available_functions=self.domain_agent.get_available_functions(),
            domain_specific_prompt=self.domain_agent.get_domain_specific_analysis_prompt(),
        )

        user_message = {
            "role": "user",
            "content": prompt,
        }

        prompt_history = [user_message]
        raw_response = self.openai_client.chat_completion(prompt_history)
        response = raw_response["choices"][0]["message"]["content"]

        return response

    def retrieve_action(
        self, query: str, scratchpad: str, step_count: int
    ) -> Tuple[str, str]:
        prompt = REACT_PROMPT.format(
            query=query,
            examples=self.domain_agent.get_examples(),
            available_functions=self.domain_agent.get_available_functions(),
            domain_specific_prompt=self.domain_agent.get_domain_specific_prompt(),
            scratchpad=scratchpad
            + f"\n\nWhat's your thought {step_count} and action {step_count}?",
            step_count=step_count,
        )

        if not self.initial_prompt:
            self.initial_prompt = prompt

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
                action = line.split(":", 1)[1].strip().replace("`", "")

        return thought, action

    def perform_action(self, action: str) -> Tuple[str, bool]:
        return self.domain_agent.perform_action(action)

    def process_query(
        self,
        query: str,
    ) -> str:
        self.scratchpad = ""
        self.total_actions = 0

        # if self.use_analysis:
        #    self.scratchpad = "\n" + self.generate_analysis(query) + "\n"

        for i in range(1, self.max_actions + 1):
            thought, action = self.retrieve_action(query, self.scratchpad, i)
            self.scratchpad += f"Thought {i}: {thought}\nAction {i}: {action}\n"
            observation, is_final = self.perform_action(action)
            self.total_actions += 1

            if not is_final:
                self.scratchpad += f"Observation {i}: {observation}\n"
            else:
                return observation

        return "Failed to complete the task."

    def get_initial_prompt(self) -> str:
        return self.initial_prompt

    def get_scratchpad(self) -> str:
        return self.scratchpad
