#!/usr/bin/env python3
import argparse
import logging
import os
import shlex
import shutil

import format
import problem
import process

logger = logging.getLogger()
LOG_FORMAT = '[%(levelname)s](%(asctime)s) %(filename)s:%(lineno)d - %(message)s'
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='A converter that convert the config.yaml from hydro to the config.toml of sastoj schema.')
    parser.add_argument('-i', '--input', help='input directory, such as ../testdata', required=False)
    parser.add_argument('-o', '--output', help='output directory', default="output", required=False)
    parser.add_argument('--rename-output', help='rename the output file to answer file', action="store_true",
                        required=False)
    parser.add_argument("--generate", help="generate the input file or answer file", action="store_true",
                        required=False)
    parser.add_argument('-c', "--case", help="case sum", type=int, default=10, required=False)
    parser.add_argument("--generate-command", help="the command to generate the input file", required=False)
    parser.add_argument("--std-command", help="the command to generate the answer file", required=False)
    return parser.parse_args()


def check_input(input_arg: str):
    if input_arg is None:
        logger.error("Please specify the input directory.")
        exit(1)
    if os.path.isfile(input_arg):
        logger.error("Input directory is a file, not a directory.")
        exit(1)


def check_custom_data_dir(output_arg) -> str:
    if os.path.basename(output_arg) != "testdata":
        output_arg = os.path.join(output_arg, "testdata")
        logger.warning(f"Output directory should be named as testdata. The data will convert to {output_arg}.")
    return output_arg


if __name__ == '__main__':
    args = parse_args()
    input_dir = args.input
    output_dir = args.output
    generate = args.generate

    if os.path.isfile(output_dir):
        logger.error("Output directory is a file, not a directory.")
        exit(1)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    elif len(os.listdir(output_dir)) > 0:
        logger.warning("Output directory is not empty, files will be overwritten.")
        for f in os.listdir(output_dir):
            if os.path.isfile(os.path.join(output_dir, f)):
                os.remove(os.path.join(output_dir, f))
            else:
                shutil.rmtree(os.path.join(output_dir, f))

    if generate:
        check_custom_data_dir(output_dir)
        if args.generate_command is None:
            logger.info("Do not find generate data command, try to find input file")
            check_input(input_dir)
            cases = process.convert_input_files(input_dir, output_dir)
            problem.merge_cases(cases)
        else:
            cases = process.generate_input_file(shlex.split(args.generate_command), output_dir, args.case)
        cases = process.generate_answer_file(shlex.split(args.std_command), output_dir, cases)
        process.generate_config_by_answer_file(cases).save(output_dir)
    else:
        check_input(input_dir)
        logger.info(f"Start to convert the data. Input directory: {input_dir}, output directory: {output_dir}")
        if format.is_custom_data(input_dir):
            output_dir = check_custom_data_dir(output_dir)
            format.convert_custom_dir(input_dir, output_dir, args)
        elif format.is_hydro_export(input_dir):
            format.convert_hydro_export_dir(input_dir, output_dir, args)
        else:
            logger.error("Unknown data format.")
