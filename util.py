import logging
import re

logger = logging.getLogger()


def extract_number(s):
    # Extract number from string
    match = re.search(r'\d+', s)
    if match:
        return int(match.group())
    else:
        return None


def convert_time(time_str: str) -> int:
    # Convert time string to millisecond
    if type(time_str) is int:
        return int(time_str)
    if time_str.endswith("ms"):
        return int(float(time_str[:-2]))
    if time_str.endswith("s"):
        return int(float(time_str[:-1]) * 1000)
    if time_str.endswith("m"):
        return int(float(time_str[:-1]) * 1000 * 60)
    if time_str.endswith("h"):
        return int(float(time_str[:-1]) * 1000 * 60 * 60)
    logger.warning(f"Time string {time_str} is not recognized. I'll try to extract the number.")
    return extract_number(time_str)


def convert_memory(memory_str: str) -> int:
    # Convert memory string to megabyte
    if type(memory_str) is int:
        return int(memory_str)
    if memory_str.lower().endswith("kb") or memory_str.lower().endswith("k") or memory_str.lower().endswith("kib"):
        return int(float(memory_str[:memory_str.lower().find("k")]) / 1024)
    if memory_str.lower().endswith("mb") or memory_str.lower().endswith("m") or memory_str.lower().endswith("mib"):
        return int(float(memory_str[:memory_str.lower().find("m")]))
    if memory_str.lower().endswith("gb") or memory_str.lower().endswith("g") or memory_str.lower().endswith("gib"):
        return int(float(memory_str[:memory_str.lower().find("g")]) * 1024)
    logger.warning(f"Memory string {memory_str} is not recognized. I'll try to extract the number.")
    return extract_number(memory_str)


def get_cases_none_sum(cases: list) -> int:
    return sum([1 for c in cases if "score" not in c or c["score"] is None])


def get_subtasks_cases_none_sum(subtasks: list) -> int:
    return sum([get_cases_none_sum(s["cases"]) for s in subtasks])


def average_score(scores: list, total_score: int) -> list:
    while None in scores:
        scores[scores.index(None)] = (total_score - sum([s for s in scores if type(s) == int])) // scores.count(None)
    return scores


def crlf_to_lf(input_file: str, output_file: str) -> None:
    input_file = open(input_file, "r")
    output_file = open(output_file, "wb")
    while True:
        line = input_file.readline()
        if not line:
            break
        output_file.write(bytes(line.replace("\r\n", "\n"), 'utf-8'))
    input_file.close()
    output_file.close()
