import time
import os
from datetime import datetime
from jinja2 import Template
from interface.ai.computer_agent import ComputerAgent
from interface.ai.controller_agent_react import ControllerAgent
from tests.agent_benchmark.computer_simulation.case_001 import Case001Computer
from tests.agent_benchmark.computer_simulation.case_002 import Case002Computer
from tests.agent_benchmark.computer_simulation.case_003 import Case003Computer


class Benchmark:
    def __init__(self, num_runs: int):
        self.num_runs = num_runs
        # self.cases = [Case001Computer(), Case002Computer(), Case003Computer()]
        self.cases = [Case002Computer()]
        self.results = []
        # Create benchmark directory
        self.benchmark_dir = self.create_benchmark_directory()
        self.agent = None  # Add this line to store the agent instance

    def create_benchmark_directory(self):
        # Create benchmarks directory if it doesn't exist
        if not os.path.exists("benchmarks"):
            os.makedirs("benchmarks")

        # Create a new directory with current datetime
        now = datetime.now()
        dir_name = now.strftime("benchmark_%Y%m%d%H%M")
        benchmark_dir = os.path.join("benchmarks", dir_name)
        os.makedirs(benchmark_dir)
        return benchmark_dir

    def run(self):
        # Save initial prompt once per benchmark
        self.agent = ControllerAgent(ComputerAgent(self.cases[0]))

        for computer in self.cases:
            case_results = []
            case_dir = os.path.join(self.benchmark_dir, computer.__class__.__name__)
            os.makedirs(case_dir)

            for run_number in range(self.num_runs):
                computer.reset_computer()
                computer_agent = ComputerAgent(computer)
                self.agent = ControllerAgent(computer_agent)

                start_time = time.time()
                self.agent.process_query(computer.test_query, [])
                end_time = time.time()

                success = computer.test_completed()
                steps = self.agent.total_actions
                duration = end_time - start_time

                # Print case, run number, and success status
                print(
                    f"{computer.__class__.__name__}(run {run_number + 1}): {'Success' if success else 'Failure'}"
                )

                # Save scratchpad
                scratchpad_filename = f"case_run_{run_number + 1}_{'success' if success else 'failure'}.txt"
                with open(os.path.join(case_dir, scratchpad_filename), "w") as f:
                    f.write(self.agent.get_scratchpad())

                case_results.append(
                    {"success": success, "steps": steps, "duration": duration}
                )

            self.results.append(
                {
                    "case_name": computer.__class__.__name__.replace("Computer", ""),
                    "query": computer.test_query,
                    "runs": case_results,
                }
            )

        with open(os.path.join(self.benchmark_dir, "prompt.txt"), "w") as f:
            f.write(self.agent.get_initial_prompt())

    def calculate_simple_score(self) -> float:
        total_runs = len(self.results) * self.num_runs
        successful_runs = sum(
            run["success"] for case in self.results for run in case["runs"]
        )

        # Calculate the score as a percentage of successful runs
        score = (successful_runs / total_runs) * 100

        return round(score, 2)  # Round to two decimal places

    def calculate_score(self) -> float:
        total_success = 0
        total_steps = 0
        total_duration = 0

        for case_result in self.results:
            for run in case_result["runs"]:
                if run["success"]:
                    total_success += 1
                    total_steps += run["steps"]
                    total_duration += run["duration"]

        avg_steps = total_steps / total_success if total_success > 0 else float("inf")
        avg_duration = (
            total_duration / total_success if total_success > 0 else float("inf")
        )

        success_rate = total_success / (len(self.results) * self.num_runs)
        step_score = max(0, 1 - (avg_steps / 20))  # Assuming 20 steps is the maximum
        duration_score = max(
            0, 1 - (avg_duration / 10)
        )  # Assuming 10 seconds is the maximum

        return (success_rate * 0.6 + step_score * 0.2 + duration_score * 0.2) * 100

    def generate_report(self):
        score = self.calculate_simple_score()
        template = Template(
            """
        <html>
        <head>
            <title>Agent Benchmark Report</title>
            <style>
                body { font-family: Arial, sans-serif; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .success { color: green; }
                .failure { color: red; }
            </style>
        </head>
        <body>
            <h1>Agent Benchmark Report</h1>
            <h2>Overall Score: {{ "%.2f"|format(score) }}%</h2>
            {% for case in results %}
            <h3>{{ case.case_name }} ({{ "%.2f"|format(case.success_rate) }}%)</h3>
            <p>Query: {{ case.query }}</p>
            <table>
                <tr>
                    <th>Run</th>
                    <th>Success</th>
                    <th>Steps</th>
                    <th>Duration (s)</th>
                </tr>
                {% for run in case.runs %}
                <tr>
                    <td>{{ loop.index }}</td>
                    <td class="{{ 'success' if run.success else 'failure' }}">
                        {{ 'Success' if run.success else 'Failure' }}
                    </td>
                    <td>{{ run.steps }}</td>
                    <td>{{ "%.2f"|format(run.duration) }}</td>
                </tr>
                {% endfor %}
            </table>
            {% endfor %}
        </body>
        </html>
        """
        )

        # Calculate success rate for each case
        for case in self.results:
            successful_runs = sum(run["success"] for run in case["runs"])
            case["success_rate"] = (successful_runs / len(case["runs"])) * 100

        report = template.render(results=self.results, score=score)
        report_path = os.path.join(self.benchmark_dir, "benchmark_report.html")
        with open(report_path, "w") as f:
            f.write(report)
        return report_path


if __name__ == "__main__":
    benchmark = Benchmark(num_runs=10)
    benchmark.run()
    report_path = benchmark.generate_report()
    print(f"Benchmark completed. Report generated: {report_path}")
