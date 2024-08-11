import logging
import os

import toml

import util

logger = logging.getLogger()


class Case:
    def __init__(self, input_file: str, answer_file: str, score: int = None, time_limit: int = 1000,
                 memory_limit: int = 100) -> None:
        self.input_file = input_file
        self.answer_file = answer_file
        self.time_limit = time_limit
        self.memory_limit = memory_limit
        self.score = score

    def __eq__(self, value: object) -> bool:
        return self.input_file == value.input_file and self.answer_file == value.answer_file and \
            self.time_limit == value.time_limit and self.memory_limit == value.memory_limit

    def __lt__(self, value: object) -> bool:
        return util.extract_number(self.output_file) < util.extract_number(value.output_file) \
            if util.extract_number(self.input_file) == util.extract_number(value.input_file) \
            else util.extract_number(self.input_file) < util.extract_number(value.input_file)

    def __add__(self, value: object) -> object:
        return Case(self.input_file, self.answer_file,
                    self.score + value.score if self.score is not None and value.score is not None else None,
                    self.time_limit, self.memory_limit)

    def __str__(self) -> str:
        return f"Cases: input file: {self.input_file}, answer file: {self.answer_file}, score: {self.score}, time limit: {self.time_limit}, memory limit: {self.memory_limit}"

    def to_toml(self) -> dict:
        return {"input": self.input_file, "answer": self.answer_file, "time": self.time_limit,
                "memory": self.memory_limit, "score": self.score}


class Subtask:
    def __init__(self, score: int, cases: list, id: int, condition: list = [], time_limit: int = 1000,
                 memory_limit: int = 256) -> None:
        self.score = score
        self.cases = cases
        self.id = id
        self.condition = condition
        self.time_limit = time_limit
        self.memory_limit = memory_limit

    def __str__(self) -> str:
        return f"Subtask: score: {self.score}, id: {self.id}, if: {self.condition}, time limit: {self.time_limit}, memory limit: {self.memory_limit}, cases sum: {len(self.cases)}"

    def to_toml(self) -> dict:
        return {"score": self.score, "cases": [c.to_toml() for c in self.cases], "time": self.time_limit,
                "memory": self.memory_limit}


class Config:
    def __init__(self, judge_type: str = "classic", task_type: str = "simple", score: int = 100,
                 time_limit: int = 1000, memory_limit: int = 256) -> None:
        self.judge_type = judge_type
        self.task_type = task_type
        self.score = score
        self.time_limit = time_limit
        self.memory_limit = memory_limit
        self.cases = []
        self.subtasks = []

    def __str__(self) -> str:
        return f"Config: judge type: {self.judge_type}, task type: {self.task_type}, score: {self.score}, time limit: {self.time_limit}, memory limit: {self.memory_limit}, cases sum: {len(self.cases)}, subtasks sum: {len(self.subtasks)}"

    def to_toml(self) -> dict:
        config_toml = {"score": self.score,
                       "judge": {
                           "judgeType": self.judge_type,
                       },
                       "resourceLimits": {
                           "time": self.time_limit,
                           "memory": self.memory_limit
                       },
                       "task": {
                           "taskType": self.task_type,
                       }
                       }
        if self.task_type == "simple":
            config_toml["task"]["cases"] = [c.to_toml() for c in self.cases]
        else:
            config_toml["task"]["subtasks"] = [s.to_toml() for s in self.subtasks]
        return config_toml

    def save(self, output_dir: str) -> None:
        with open(os.path.join(output_dir, "config.toml"), "w") as f:
            f.write(toml.dumps(self.to_toml()))


def merge_cases(cases: list) -> list:
    merged_cases = []
    for case in cases:
        if case in merged_cases:
            logger.info(f"Case {case.input_file}/{case.answer_file} have the same IO file and limit. I'll merge them.")
            merged_cases[merged_cases.index(case)] += case
        else:
            merged_cases.append(case)
    return merged_cases


def case_legal(case: dict) -> bool:
    return (("score" in case and type(case["score"]) == int and case["score"] > 0) or "score" not in case) and \
        ("input" in case and type(case["input"]) == str and case["input"].lower().endswith(".in")) and \
        ("output" in case and type(case["output"]) == str and (
                    case["output"].lower().endswith(".out") or case["input"].lower().endswith(".ans")))


def get_problem_cases(problem: Config) -> list:
    cases = []
    for subtask in problem.subtasks:
        cases.extend(subtask.cases)
    cases.extend(problem.cases)
    return cases


def get_case_limit(case: dict) -> tuple:
    case_time_limit = None
    case_memory_limit = None
    if "time" in case and case["time"] is not None:
        case_time_limit = util.convert_time(case["time"])
        logger.warning(
            f"Case {case["input"]}/{case["ouuput"]} has time limit, time limit for case is not supported in sastoj, but it will be kept.")
    if "memory" in case and case["memory"] is not None:
        case_memory_limit = util.convert_memory(case["memory"])
        logger.warning(
            f"Case {case["input"]}/{case["ouuput"]} has memory limit, memory limit for case is not supported in sastoj, but it will be kept.")
    return case_time_limit, case_memory_limit
