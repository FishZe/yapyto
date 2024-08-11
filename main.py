#!/usr/bin/env python3
import argparse
import logging
import os

import format

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
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    input_dir = args.input
    output_dir = args.output
    if input_dir is None:
        logger.error("Please specify the input directory.")
        exit(1)
    if os.path.isfile(input_dir):
        logger.error("Input directory is a file, not a directory.")
        exit(1)
    if os.path.isfile(output_dir):
        logger.error("Output directory is a file, not a directory.")
        exit(1)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    elif len(os.listdir(output_dir)) > 0:
        logger.warning("Output directory is not empty, files will be overwritten.")
        for f in os.listdir(output_dir):
            os.remove(os.path.join(output_dir, f))
    logger.info(f"Start to convert the data. Input directory: {input_dir}, output directory: {output_dir}")

    if format.is_custom_data(input_dir):
        format.convert_custom_dir(input_dir, output_dir, args)
    elif format.is_hydro_export(input_dir):
        format.convert_hydro_export_dir(input_dir, output_dir, args)
    else:
        logger.error("Unknown data format.")
