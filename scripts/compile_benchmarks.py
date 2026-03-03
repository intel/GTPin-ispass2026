#!/usr/bin/env python3
import os.path
import subprocess
import argparse
import ast
from common import read_yaml_cfg


def parse_and_validate_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("HeC benchmark compilation script")
    parser.add_argument("--hecbench_dir", type=str,
                        default="/work/HeCBench",
                        help="location of the HeCBench repo")
    parser.add_argument("--action", type=str, choices=["clean", "build"], default="build",
                        help="The action to perform")
    parser.add_argument("--programming_model", type=str,
                        default="sycl",
                        help="Programming model to compile/clean (single value). Default: sycl")
    return parser.parse_args()


def main():
    args = parse_and_validate_args()
    benchmark_cfg = read_yaml_cfg("scripts/specs.yaml")["HeCBench"]

    requested_pm = args.programming_model
    compiled_any = False
    skipped = []

    for bench, bench_cfg in benchmark_cfg.items():
        pm_dict = bench_cfg.get("programming_models", {})

        if requested_pm not in pm_dict:
            skipped.append(bench)
            continue

        cfgs = pm_dict[requested_pm]

        # Safer than eval() for YAML strings representing Python literals (lists/strings)
        compile_flags = ast.literal_eval(cfgs["compilation_flags"])

        print(f"{args.action.capitalize()}ing {bench}-{requested_pm}")
        benchmark_folder = os.path.join(args.hecbench_dir, "src", f"{bench}-sycl")

        make_command = (["make"] + list(compile_flags)) if args.action == "build" else ["make", "clean"]
        status_code = subprocess.call(args=make_command, cwd=benchmark_folder)
        if status_code:
            raise ChildProcessError(f"Failed {args.action}ing {bench}-{requested_pm}.")

        compiled_any = True

    if not compiled_any:
        raise ValueError(
            f"Programming model '{requested_pm}' was not found for any benchmark in scripts/specs.yaml "
            f"(did you misspell it?)."
        )

    if skipped:
        print(f"Skipped {len(skipped)} benchmarks (no '{requested_pm}' variant): {', '.join(skipped)}")


if __name__ == "__main__":
    main()