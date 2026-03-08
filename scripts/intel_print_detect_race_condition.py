############################ begin_copyright_notice ############################
### Copyright (C) 2026 Intel Corporation
###
### This software and the related documents are Intel copyrighted materials, and your
### use of them is governed by the express license under which they were provided to
### you ("License"). Unless the License provides otherwise, you may not use, modify,
### copy, publish, distribute, disclose or transmit this software or the related
### documents without Intel's prior written permission.
###
### This software and the related documents are provided as is, with no express or
### implied warranties, other than those that are expressly stated in the License.
############################ end_copyright_notice ##############################

import math
import argparse
import os
import pickle
import csv
import sys

def parse_and_validate_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("Intel Race Condition Detection print script")
    parser.add_argument("--app", type=str,
                        default="./GTPin/race_condition",
                        help="Path of the compiled race_condition application")
    parser.add_argument("--out_csv", type=str,
                        default="detect-memory-race-model-results.csv",
                        help="output CSV file path")

    args = parser.parse_args()
    return args


RESULT_PKLE_FILE_NAME = "detect-memory-race-model-results.pkl"


CSV_KEYS = [
    "Number of detected races",
    "cmd",
]

def main():
    args = parse_and_validate_args()

    # Collect rows for CSV

    app_folder = args.app
    pkl_path   = os.path.join(app_folder, RESULT_PKLE_FILE_NAME)

    if not os.path.isfile(pkl_path):
        raise FileNotFoundError(f"Missing results pickle: {pkl_path}")

    objects = []

    with open(pkl_path, "rb") as f:
        while True:
            try:
                obj = pickle.load(f)
                objects.append(obj)
            except EOFError:
                break

    rows = []

    for obj in objects:
        row = {}
        # Extract requested keys (leave blank if missing)
        for k in CSV_KEYS:
            row[k] = obj.get(k, "")

        rows.append(row)

    # Write CSV
    fieldnames = CSV_KEYS
    with open(args.out_csv, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote CSV with {len(rows)} rows to: {args.out_csv}")


if __name__ == "__main__":
    main()