import logging
import os
import subprocess
import time

import psutil

import problem
import util

logger = logging.getLogger()


class processTask:
    def __init__(self, command: list, input_file: str | None, output_file: str, terminate_time: int = 10):
        self.command = command
        self.input_file = input_file
        self.output_file = output_file
        self.runtime = 0
        self.memory = 0
        self.terminate_time = terminate_time

    def run(self) -> int:
        infile = open(self.input_file, 'r') if self.input_file else None
        process = subprocess.Popen(self.command, stdin=infile, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        psutil_process = psutil.Process(process.pid)

        try:
            while process.poll() is None:
                cpu_times = psutil_process.cpu_times()
                memory_info = psutil_process.memory_info()
                self.runtime = max(self.runtime, cpu_times.user + cpu_times.system)
                self.memory = max(self.memory, memory_info.rss / 1024 ** 2)
                time.sleep(0.01)

                if cpu_times.user + cpu_times.system > self.terminate_time:
                    logger.warning("Command is running too long, try to terminate it.")
                    process.terminate()
                    process.wait(timeout=5)
                    break
        except psutil.NoSuchProcess:
            logger.error("Process is not found, may be terminated by system.")
        except Exception as e:
            logger.error(f"Error occurred when running the command: {e}")

        if process.poll() is None:
            logger.warning("Command is still running, try to kill it.")
            process.kill()
        infile.close() if infile else None

        stdout, stderr = process.communicate()
        if process.returncode != 0:
            logger.error(f"Subprocess failed with return code {process.returncode},stderr are as follows:")
            logger.warning(stderr.decode())
        else:
            if self.output_file is not None:
                stdout = stdout.replace(b'\r\n', b'\n')
                with open(self.output_file, 'wb') as f:
                    f.write(stdout)
        return process.returncode


def generate_input_file(command: list, output_dir: str, case_sum) -> list:
    logger.info(f"Start to generate input files to {output_dir} with command {command}.")
    cases = []
    for i in range(case_sum):
        task = processTask(command, None, os.path.join(output_dir, f"{i + 1}.in"))
        if task.run() != 0:
            logger.error(f"Failed to generate input file {i + 1}.in.")
        else:
            cases.append(problem.Case(f"{i + 1}.in", None))
    logger.info(f"Generate {len(cases)} input files to {output_dir}.")
    return cases


def generate_answer_file(command: list, output_dir: str, cases: list) -> list:
    logger.info(f"Start to generate answer files to {output_dir} with command {command}.")
    new_cases = []
    for c in cases:
        task = processTask(command, os.path.join(output_dir, c.input_file),
                           os.path.join(output_dir, c.input_file.replace(".in", ".ans")))
        if task.run() != 0:
            logger.error(f"Failed to generate answer file {c.answer_file}.")
        else:
            new_cases.append(
                problem.Case(c.input_file, c.answer_file, time_limit=task.runtime, memory_limit=task.memory))
    logger.info(f"Generate {len(new_cases)} answer files to {output_dir}.")
    return new_cases


def convert_input_files(input_dir: str, output_dir: str) -> list:
    logger.info(f"Start to process input directory {input_dir} to output directory {output_dir}.")
    files = os.listdir(input_dir)
    cases = []
    for f in files:
        if f.endswith(".in"):
            util.crlf_to_lf(os.path.join(input_dir, f), os.path.join(output_dir, f))
            cases.append(problem.Case(f, None))
    logger.info(f"Process {len(cases)} input files to {output_dir}.")
    return cases


def generate_config_by_answer_file(cases: list) -> problem.Config:
    logger.info(f"Start to generate config by answer files.")
    max_time = 0
    max_memory = 0
    for c in cases:
        max_time = max(max_time, c.time_limit)
        max_memory = max(max_memory, c.memory_limit)
    max_time = int(((max_time // 100) + 1) * 100)
    max_memory = int(((max_memory // 256) + 1) * 256)
    logger.info(f"Max time limit: {max_time}, max memory limit: {max_memory}.")
    scores = util.average_score([None for _ in range(len(cases))], 100)
    for i in range(len(cases)):
        cases[i].score = scores[i]
        cases[i].time_limit = int(((cases[i].time_limit // 10) + 1) * 10)
        cases[i].memory_limit = int(((cases[i].memory_limit // 16) + 1) * 16)
    logger.info(f"Generate config with {len(cases)} cases.")
    config = problem.Config("classic", "simple", 100, max_time, max_memory)
    config.cases = cases
    return config
