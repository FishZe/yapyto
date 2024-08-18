import json
import logging
import os

import yaml

import problem
import util

logger = logging.getLogger()


def load_yaml_config_file(file: str) -> None | problem.Config:
    config = yaml.load(open(file, "r"), Loader=yaml.FullLoader)

    # convert judge type and checker type
    problem_type = config["type"] if "type" in config and config["type"] is not None else "default"
    checker_type = config["checker_type"] if "checker_type" in config and config[
        "checker_type"] is not None else "default"
    judge_type = "classic"
    if problem_type == "interactive":
        # judge_type = "interactive"
        logger.warning("Interactive problem is not supported, this problem **CAN NOT** be converted.")
        return
        # TODO: interactive problem and special judge
    elif problem_type != "default" or checker_type != "default":
        logger.warning(
            f"Unsupported problem type {problem_type} or checker_type {checker_type}, this problem **CAN NOT** be converted.")
        return
    logger.info(f"Config file type: {problem_type}, checker type: {checker_type}, convert to: {judge_type}")

    # convert time limit, memory limit and score
    time_limit = util.convert_time(config["time"]) if "time" in config and config["time"] is not None else None
    memory_limit = util.convert_memory(config["memory"]) if "memory" in config and config[
        "memory"] is not None else None
    score = config["score"] if "score" in config else None
    logger.info(f"Load arg from config: Time limit: {time_limit}, memory limit: {memory_limit}, score: {score}")

    if "subtasks" in config:
        logger.info(f"Find {len(config['subtasks'])} subtasks in config file.")
        # sastoj not support **type** arg in subtask
        # type min: keep, max: NOT support, sum: convert to the score in cases
        # time limit and memory limit in subtask convert to the limit in cases or global limit

        hydro_subtasks = []
        subtasks_scores = []
        subtasks_cases = []
        min_subtask = False
        sum_subtask = False
        for i, subtask in enumerate(config["subtasks"]):
            logger.debug(f"Now checking subtask {i}, id: {subtask['id'] if 'id' in subtask else None}")
            subtask["id"] = subtask["id"] if "id" in subtask and type(subtask["id"]) is int else i + 1
            # check subtask and cases
            if "type" not in subtask or subtask["type"] is None:
                logger.warning(f"Subtask {i} Subtask type is not specified, use min as default.")
                subtask["type"] = "min"
                min_subtask = True
            elif subtask["type"] == "max":
                logger.warning(f"Subtask {i} Subtask type max is not supported, this subtask will be ignored.")
                continue
            elif subtask["type"] == "sum":
                sum_subtask = True
            elif subtask["type"] == "min":
                min_subtask = True
            if "cases" not in subtask or len(subtask["cases"]) == 0:
                logger.warning(f"Subtask {i} Subtask cases is not specified, this subtask will be ignored.")
                continue
            if "score" in subtask and type(subtask["score"]) is int and subtask["score"] < len(subtask["cases"]):
                logger.warning(
                    f"Subtask {i} Subtask score is less than the number of cases, this subtask will be ignored.")
                continue
            all_cases_have_score = True
            cases_score_sum = 0
            legal_cases = []
            for j, case in enumerate(subtask["cases"]):
                if problem.hydro_case_legal(case):
                    legal_cases.append(case)
                    if "score" not in case:
                        all_cases_have_score = False
                    else:
                        cases_score_sum += case["score"]
                elif "score" in case and case["score"] is not None:
                    logger.warning(f"Subtask {i} Case {j} score is not a positive integer, this case will be ignored.")
            if len(legal_cases) == 0:
                logger.warning(f"Subtask {i} Subtask has no valid cases, this subtask will be ignored.")
                continue
            logger.info(f"Subtask {i} has {len(legal_cases)} valid cases.")
            if all_cases_have_score:
                if "score" in subtask and subtask["score"] is not None:
                    if cases_score_sum != subtask["score"]:
                        logger.warning(
                            f"Subtask {i} The sum of cases score is not equal to the subtask score, this subtask will be ignored.")
                        continue
                else:
                    subtask["score"] = cases_score_sum
            del subtask["cases"]
            hydro_subtasks.append(subtask)
            subtasks_cases.append(legal_cases)
            subtasks_scores.append(subtask["score"] if "score" in subtask else None)

        if len(hydro_subtasks) == 0:
            logger.warning("No valid subtask in config file.")
            return
        logger.info(f"Find {len(hydro_subtasks)} valid subtasks in config file.")
        if min_subtask and sum_subtask:
            logger.error("Find min and sum subtask in config file, this problem will be ignored.")
            return

        # check subtasks score
        if score is None:
            logger.info("No score in config file, I will try to figure it.")
            if None not in subtasks_scores:
                score = sum(subtasks_scores)
                logger.info(f"Calculated problem score: {score}")
            else:
                logger.info("Some subtasks score is not specified, try using 100 as default.")
                score = 100
        if sum([s for s in subtasks_scores if type(s) is int]) > score:
            logger.error(
                "The sum of subtasks score is greater than the score in config file, this problem will be ignored.")
            return
        elif sum([s for s in subtasks_scores if type(s) is int]) == score and None not in subtasks_scores:
            logger.info("The sum of subtasks score is equal to the score in config file.")
        elif sum([s for s in subtasks_scores if type(s) is int]) == score and None in subtasks_scores:
            logger.error(
                "The sum of subtasks score is equal to the score in config file, but some subtasks score is not specified, this problem will be ignored.")
            return
        elif sum([s for s in subtasks_scores if type(s) is int]) < score and None not in subtasks_scores:
            logger.error(
                "The sum of subtasks score is less than the score in config file, this problem will be ignored.")
            return
        elif sum([s for s in subtasks_scores if type(s) is int]) < score and None in subtasks_scores:
            logger.info(
                "The sum of subtasks score is less than the score in config file, but some subtasks score is not specified.")
            if min_subtask:
                logger.info("Subtasks are min type, I will try to figure score.")
                subtasks_scores = util.average_score(subtasks_scores, score)
            else:
                logger.info("Subtasks are sum type, the score will be calculated by the sum of cases later.")
        for i, subtask in enumerate(hydro_subtasks):
            subtask["score"] = subtasks_scores[i]

        task_type = ""
        cases = []
        subtasks = []
        max_time_limit = 0
        max_memory_limit = 0
        # convert subtask to sastoj schema
        if sum_subtask:
            # type sum: keep and convert to task type simple
            task_type = "simple"
            logger.info("Subtask type is sum, convert to task type simple. But some args will be ignored.")
            for i, subtask in enumerate(hydro_subtasks):
                logger.debug(f"Now processing subtask {i}, id: {subtask['id'] if 'id' in subtask else None}")
                if "time" in subtask or "memory" in subtask or "if" in subtask:
                    logger.warning(
                        f"Subtask {i} has time, memory or if limit, but this subtask will be change to cases, these args will be ignored.")
                    subtask_time_limit = util.convert_time(subtask["time"]) if "time" in subtask and subtask[
                        "time"] is not None else None
                    subtask_memory_limit = util.convert_memory(subtask["memory"]) if "memory" in subtask and subtask[
                        "memory"] is not None else None
                    max_time_limit = max(max_time_limit, subtask_time_limit if subtask_time_limit is not None else 0)
                    max_memory_limit = max(max_memory_limit,
                                           subtask_memory_limit if subtask_memory_limit is not None else 0)
                if "score" in subtask and type(subtask["score"]) is int:
                    cases_score = []
                    for case in subtasks_cases[i]:
                        cases_score.append(case["score"] if "score" in case and type(case["score"]) is int else None)
                    if sum([s for s in cases_score if s is not None]) == subtask["score"] and None not in cases_score:
                        logger.info(f"Subtask {i} has valid score.")
                    elif sum([s for s in cases_score if s is not None]) < subtask["score"] and None in cases_score and \
                            subtask["score"] - sum([s for s in cases_score if s is not None]) >= cases_score.count(
                        None):
                        logger.info(f"Subtask {i} has invalid score, try to figure it.")
                        cases_score = util.average_score(cases_score, subtask["score"])
                    else:
                        logger.error(
                            f"Subtask {i} has invalid score, all the score of the cases will be calculated by the sum of the cases.")
                        cases_score = util.average_score([None for _ in range(len(subtasks_cases[i]))],
                                                         subtask["score"])
                    for j, case in enumerate(subtasks_cases[i]):
                        case_time_limit, case_memory_limit = problem.get_case_limit(case)
                        max_time_limit = max(max_time_limit, case_time_limit if case_time_limit is not None else 0)
                        max_memory_limit = max(max_memory_limit,
                                               case_memory_limit if case_memory_limit is not None else 0)
                        cases.append(problem.Case(case["input"], case["output"], cases_score[j], case_time_limit,
                                                  case_memory_limit))
                else:
                    logger.info(f"Subtask {i} has no score.")
                    for case in subtasks_cases[i]:
                        case_time_limit, case_memory_limit = problem.get_case_limit(case)
                        cases.append(
                            problem.Case(case["input"], case["output"], case["score"] if "score" in case else None,
                                         case_time_limit, case_memory_limit))
            problem_cases_scores = [c.score for c in cases]
            if None in problem_cases_scores:
                logger.info("Some cases score in problem is not specified, try to figure it.")
                if score - sum([c for c in problem_cases_scores if c is not None]) < problem_cases_scores.count(None):
                    logger.warning(
                        "The sum of cases score is less than the score in config file, all the score of the cases will be calculated by the sum of the cases.")
                    problem_cases_scores = util.average_score([None for _ in range(len(problem_cases_scores))], score)
                else:
                    problem_cases_scores = util.average_score(problem_cases_scores, score)
                for i, case in enumerate(cases):
                    case.score = problem_cases_scores[i]
            cases = problem.merge_cases(cases)

        elif min_subtask:
            # type min: keep and convert to task type subtask
            task_type = "subtask"
            logger.info("Subtask type is min, convert to task type subtask.")
            for i, subtask in enumerate(hydro_subtasks):
                logger.debug(f"Now processing subtask {i}, id: {subtask['id'] if 'id' in subtask else None}")
                if "time" in subtask or "memory" in subtask or "if" in subtask:
                    logger.warning(
                        f"Subtask {i} has time, memory or if limit, sastoj not support, but these args will be kept.")
                subtask_time_limit = util.convert_time(subtask["time"]) if "time" in subtask and subtask[
                    "time"] is not None else None
                subtask_memory_limit = util.convert_memory(subtask["memory"]) if "memory" in subtask and subtask[
                    "memory"] is not None else None
                max_time_limit = max(max_time_limit, subtask_time_limit if subtask_time_limit is not None else 0)
                max_memory_limit = max(max_memory_limit,
                                       subtask_memory_limit if subtask_memory_limit is not None else 0)
                subtask_if = subtask["if"] if "if" in subtask and type(subtask["if"]) is list else []
                cases = []
                for case in subtasks_cases[i]:
                    if "score" in case:
                        logger.warning(
                            f"Subtask {i} Case {case['input']}/{case['output']} has score, it will be ignored.")
                    case_time_limit, case_memory_limit = problem.get_case_limit(case)
                    cases.append(problem.Case(case["input"], case["output"], None, case_time_limit, case_memory_limit))
                now_subtask = problem.Subtask(subtask["score"], sorted(cases), subtask["id"], subtask_if,
                                              subtask_time_limit, subtask_memory_limit)
                subtasks.append(now_subtask)

        time_limit = max(max_time_limit, time_limit if time_limit is not None else 0)
        memory_limit = max(max_memory_limit, memory_limit if memory_limit is not None else 0)
        config = problem.Config(judge_type, task_type, score, time_limit if time_limit != 0 else None,
                                memory_limit if memory_limit != 0 else None)
        if task_type == "simple":
            config.cases = sorted(cases)
        else:
            config.subtasks = subtasks
        return config
    else:
        logger.info("No subtasks in config file.")
        return problem.Config(judge_type, score=score, time_limit=time_limit, memory_limit=memory_limit)


def load_json_config_file(file: str) -> None | problem.Config:
    config_file = json.load(open(file, "r"))
    judge_type = config_file["judge"]["judgeType"] if "judge" in config_file and "judgeType" in config_file["judge"] else "classic"
    task_type = config_file["task"]["taskType"] if "task" in config_file and "taskType" in config_file["task"] else None
    if task_type is None:
        if "cases" in config_file["task"]:
            task_type = "simple"
        elif "subtasks" in config_file["task"]:
            task_type = "subtask"
        else:
            logger.warning("No valid task type in config file.")
            return None
    config = problem.Config(judge_type, task_type, config_file["score"] if "score" in config_file else None,
                            config_file["resourceLimits"]["time"]
                            if "resourceLimits" in config_file and "time" in config_file["resourceLimits"] else None,
                            config_file["resourceLimits"]["memory"] if "resourceLimits" in config_file and \
                            "memory" in config_file["resourceLimits"] else None)

    if task_type == "simple":
        scores = []
        cases = []
        for case in config_file["task"]["cases"]:
            if problem.sastoj_case_legal(case):
                case_time_limit, case_memory_limit = problem.get_case_limit(case)
                cases.append(problem.Case(case["input"], case["answer"], case["score"] if "score" in case else None,
                                          case_time_limit, case_memory_limit))
                scores.append(case["score"] if "score" in case else None)
            else:
                logger.warning(f"Case {case['input']}/{case['answer']} is not valid, this case will be ignored.")
        if len(cases) == 0:
            logger.error("No valid cases in config file.")
            return None
        scores = util.average_score(scores, config_file["score"] if "score" in config_file else 100)
        for i, case in enumerate(cases):
            case.score = scores[i]
        config.cases = sorted(cases)
    elif task_type == "subtask":
        subtasks = []
        for subtask in config_file["task"]["subtasks"]:
            subtask_time_limit = subtask["time"] if "time" in subtask else None
            subtask_memory_limit = subtask["memory"] if "memory" in subtask else None
            subtask_if = subtask["if"] if "if" in subtask else []
            subtask_cases = []
            subtask_scores = []
            for case in subtask["cases"]:
                if problem.sastoj_case_legal(case):
                    case_time_limit, case_memory_limit = problem.get_case_limit(case)
                    subtask_cases.append(
                        problem.Case(case["input"], case["answer"], case["score"] if "score" in case else None,
                                     case_time_limit, case_memory_limit))
                    subtask_scores.append(case["score"] if "score" in case else None)
                else:
                    logger.warning(f"Case {case['input']}/{case['answer']} is not valid, this case will be ignored.")
            if len(subtask_cases) == 0:
                logger.error(f"No valid cases in subtask {subtask['id'] if 'id' in subtask else None}.")
                continue
            if None in subtask_scores:
                logger.info(
                    f"Some cases score in subtask {subtask['id'] if 'id' in subtask else None} is not specified, try to figure it.")
                if subtask["score"] - sum([s for s in subtask_scores if s is not None]) < subtask_scores.count(None):
                    logger.warning(
                        f"The sum of cases score in subtask {subtask['id'] if 'id' in subtask else None} is less than the subtask score, all the score of the cases will be calculated by the sum of the cases.")
                    subtask_scores = util.average_score([None for _ in range(len(subtask_scores))], subtask["score"])
                else:
                    subtask_scores = util.average_score(subtask_scores, subtask["score"])
                for i, case in enumerate(subtask_cases):
                    case.score = subtask_scores[i]
            subtasks.append(problem.Subtask(subtask["score"], sorted(subtask_cases), subtask["id"], subtask_if,
                                            subtask_time_limit, subtask_memory_limit))
        config.subtasks = subtasks
    return config


def generate_cases(input_dir: str) -> list:
    files = os.listdir(input_dir)
    cases = []
    for file in files:
        if file.lower().endswith(".out") or file.lower().endswith(".ans"):
            file_name = file[:file.rfind(".")]
            if file_name + ".in" not in files:
                logger.warning(f"file has no input file {file_name}.in .")
            cases.append(problem.Case(file_name + ".in", file, None))
    cases_score = util.average_score([None for _ in range(len(cases))], 100)
    for i, case in enumerate(cases):
        case.score = cases_score[i]
    cases = sorted(problem.merge_cases(cases))
    return cases


def generate_config_file(input_dir: str) -> None | problem.Config:
    cases = generate_cases(input_dir)
    if len(cases) == 0:
        logger.error("No valid cases in the directory. Can not generate config file.")
        return
    config = problem.Config("classic", "simple", 100)
    config.cases = cases
    return config
