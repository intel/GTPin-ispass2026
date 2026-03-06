import math
from common import read_yaml_cfg
import argparse
import os
import pickle
import csv


def parse_and_validate_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("Opcodeprof runner script")
    parser.add_argument("--hecbench_dir", type=str,
                        default="/work/HeCBench",
                        help="location of the HeCBench repo")
    parser.add_argument("--specs_yaml", type=str,
                        default="scripts/specs.yaml",
                        help="supply your own specs yaml file")
    parser.add_argument("--out_csv", type=str,
                        default="intel-full-opcodeprof-results.csv",
                        help="output CSV file path")

    args = parser.parse_args()
    return args


RESULT_PKLE_FILE_NAME = "intel-full-opcodeprof-results.pkl"


CSV_KEYS = [
    "Number of Instructions - LLI Opcodeprof",
    "Un-instrumented APP Kernel Runtime (us)",
    "Instrumented GTPin Kernel Runtime - LLI Opcodeprof (us)",
    "Number of Instructions - HLI Opcodeprof",
    "Instrumented GTPin Kernel Runtime - HLI Opcodeprof (us)",
]


def main():
    args = parse_and_validate_args()
    benchmark_cfg = read_yaml_cfg(args.specs_yaml)

    benchmarks = benchmark_cfg["Opcode"]["benchmarks"]
    gpu_system = "intel"

    # Collect rows for CSV
    rows = []

    for bench in benchmarks:

        benchmark_folder = os.path.join(
            args.hecbench_dir, "src", f"{bench}-sycl"
        )
        pkl_path = os.path.join(benchmark_folder, RESULT_PKLE_FILE_NAME)

        if not os.path.isfile(pkl_path):
            raise FileNotFoundError(
                f"Missing results pickle: {pkl_path}"
            )

        with open(pkl_path, "rb") as f:
            data_point = pickle.load(f)

        row = {
            "benchmark": bench,
            "GPU": gpu_system,
        }

        # Extract requested keys (leave blank if missing)
        for k in CSV_KEYS:
            row[k] = data_point.get(k, "")

        rows.append(row)

    # Write CSV
    fieldnames = ["benchmark", "GPU"] + CSV_KEYS
    with open(args.out_csv, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote CSV with {len(rows)} rows to: {args.out_csv}")


if __name__ == "__main__":
    main()
