import argparse
import logging
import os

import config
import problem
import util

logger = logging.getLogger()


def is_custom_data(input_dir: str) -> bool:
    # Only .in .out/.ans and config.yaml (optional) file in the directory
    # No extra files and directories, or the directory is not custom data file
    find_output = False
    for f in os.listdir(input_dir):
        if os.path.isdir(f):
            logger.warning(f"{f} is a directory, {input_dir} is not a custom data directory.")
            return False
        elif f.endswith(".out") or f.endswith(".ans"):
            find_output = True
    if not find_output:
        logger.warning(f"No output file is found in {input_dir}.")
        return False
    logger.info(f"{input_dir} is a custom data directory.")
    return True


def is_hydro_export(input_dir: str) -> bool:
    logger.info(f"Check {input_dir} is a hydro export directory.")
    for f in os.listdir(input_dir):
        if os.path.isdir(os.path.join(input_dir, f)) and \
                os.path.exists(os.path.join(input_dir, f, "testdata")) and \
                is_custom_data(os.path.join(input_dir, f, "testdata")):
            logger.info(f"find {f} is a problem data file")
            return True
    logger.info(f"Can not find problem file, {input_dir} is not a hydro export directory.")
    return False


def get_hydro_export_problems(input_dir: str) -> list:
    problems = []
    for f in os.listdir(input_dir):
        if os.path.isdir(os.path.join(input_dir, f)) and \
                os.path.exists(os.path.join(input_dir, f, "testdata")) and \
                is_custom_data(os.path.join(input_dir, f, "testdata")):
            problems.append(os.path.join(input_dir, f))
    logger.info(f"Find {len(problems)} problems in {input_dir}.")
    return problems


def check_config_case_file(config: problem.Config, dir: str) -> list:
    files = os.listdir(dir)
    not_found = []
    cases = []
    for subtask in config.subtasks:
        for case in subtask.cases:
            cases.append(case)
    for case in config.cases:
        cases.append(case)
    for case in cases:
        if case.input_file not in files:
            logger.warning(f"Case input file {case.input_file} is not found in {dir}.")
            not_found.append(case.input_file)
        if case.answer_file not in files:
            logger.warning(f"Case output file {case.answer_file} is not found in {dir}.")
            not_found.append(case.answer_file)
    return not_found


def generate_empty_file(files: list, dir: str):
    for file in files:
        with open(os.path.join(dir, file), "wb") as f:
            f.write(bytes('\n', 'utf-8'))


def load_data_dir(dir: str):
    config_file = None
    if os.path.isfile(os.path.join(dir, "config.yaml")):
        logger.info(f"Find config.yaml from {dir}")
        config_file = config.load_config_file(os.path.join(dir, "config.yaml"))
        if config_file is None:
            logger.warning(f"Failed to load config.yaml from {dir}")
        else:
            logger.info(f"Config.yaml is loaded from {dir}")
            if config_file.task_type is None or config_file.judge_type is None or \
                    (len(config_file.cases) == 0 and len(config_file.subtasks) == 0):
                logger.warning(f"Config.yaml from {dir} is not complete, try to find cases.")
                cases = config.generate_cases(dir)
                if len(cases) == 0:
                    logger.error(f"No cases are found in {dir}")
                    return
                config_file.task_type = "simple"
                config_file.cases = cases
    if config_file is None:
        logger.info(f"Try to generate config from {dir} by file name.")
        config_file = config.generate_config_file(dir)
        if config_file is None:
            logger.error(f"Failed to generate config from {dir}")
            return
        logger.info(f"Config is generated from {dir}, find {len(config_file.cases)} cases.")
    not_found_files = check_config_case_file(config_file, dir)
    if len(not_found_files) != 0:
        logger.warning(f"Case IO files {not_found_files} are not found in {dir}, try to generate empty file.")
        generate_empty_file(not_found_files, dir)
    return config_file


def convert_data_dir(config_file: problem.Config, input_dir: str, output_dir: str, rename_answer: bool = True) -> None:
    logger.info(f"Convert data from {input_dir} to {output_dir}")
    cases = problem.get_problem_cases(config_file)
    logger.debug(f"Cases sum: {len(cases)}, rename .out to .ans: {rename_answer}")
    files = []
    for case in cases:
        files.append((os.path.join(input_dir, case.input_file), os.path.join(output_dir, case.input_file)))
        if not rename_answer:
            files.append((os.path.join(input_dir, case.answer_file), os.path.join(output_dir, case.answer_file)))
        else:
            files.append((os.path.join(input_dir, case.answer_file),
                          os.path.join(output_dir, case.answer_file.replace(".out", ".ans"))))
    for file in files:
        util.crlf_to_lf(file[0], file[1])
    logger.info(
        f"Data is converted from {input_dir} to {output_dir}, output directory size: {os.path.getsize(output_dir)} bytes.")


def convert_custom_dir(input_dir: str, output_dir: str, args: argparse.Namespace) -> None:
    logger.info("Custom data format is detected, try to find config.yaml or generate config")
    config_file = load_data_dir(input_dir)
    if config_file is None:
        logger.error("Failed to load config.yaml and generate config, exit.")
        exit(1)
    logger.info(f"Config file is loaded from {input_dir}, save to {output_dir}")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    config_file.save(output_dir)
    logger.info("Config file is saved, start to convert the data.")
    convert_data_dir(config_file, input_dir, output_dir, args.rename_output)
    logger.info("Data is converted.")


def convert_hydro_export_dir(input_dir: str, output_dir: str, args: argparse.Namespace) -> None:
    problems = get_hydro_export_problems(input_dir)
    success_count = 0
    for problem_dir in problems:
        config_file = load_data_dir(os.path.join(problem_dir, "testdata"))
        if config_file is None:
            logger.error(f"Failed to load config from {problem_dir}, skip.")
            continue
        if "problem.md" in os.listdir(problem_dir) or "problem.yaml" in os.listdir(problem_dir):
            logger.warning(
                "Problem description file is found, sastoj do NOT support upload problem with cases, this file will be ignored.")
        output = os.path.join(output_dir, os.path.join(os.path.basename(problem_dir), "testdata"))
        if not os.path.exists(output):
            os.makedirs(output)
        convert_data_dir(config_file, os.path.join(problem_dir, "testdata"), output, args.rename_output)
        config_file.save(output)
        logger.info(
            f"Data is converted from {problem_dir} to {output_dir}, output directory size: {os.path.getsize(output_dir)} bytes.")
        success_count += 1
    logger.info(f"Convert {success_count} problems from {input_dir} to {output_dir}.")
