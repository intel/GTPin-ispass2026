import math
import argparse
import os
import pickle
import csv
import sys

def parse_and_validate_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("Memory cache model script")
    parser.add_argument("--app", type=str,
                        default=".",
                        help="Full path of the compiled ze_gemm application")
    parser.add_argument("--out_csv", type=str,
                        default="memory-cache-model-results.csv",
                        help="output CSV file path")

    args = parser.parse_args()
    return args


RESULT_PKLE_FILE_NAME = "memory-cache-model-results.pkl"


CSV_KEYS = [
    "Cache size (in KB)",
    "Cacheline size (in Byte)",
    "Number of hits",
    "Number of misses",
    "Number of cacheline acceses",
    "Hits distribution(%)",
    "Misses distribution(%)",
    "cmd",
]

def main():
    args = parse_and_validate_args()

    # Collect rows for CSV

    ze_gemm_folder = args.app
    pkl_path = os.path.join(ze_gemm_folder, RESULT_PKLE_FILE_NAME)

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