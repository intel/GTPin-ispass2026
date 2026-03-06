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

#!/usr/bin/env python3
import os.path
import subprocess
import argparse
import ast
from common import read_yaml_cfg


def parse_and_validate_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("HeC benchmark compilation script")
    parser.add_argument("--hecbench_dir", type=str,
                        default="./HeCBench",
                        help="location of the HeCBench repo")
    parser.add_argument("--action", type=str, choices=["clean", "build"], default="build",
                        help="The action to perform")
    parser.add_argument("--system", type=str,
                        default="intel",
                        help="GPU System to compile/clean [intel, amd, nvidia]. Default: intel")
    parser.add_argument("--test", type=bool, action=argparse.BooleanOptionalAction,
                        default=False,
                        help="Test run applications (default: False)")
    parser.add_argument("--reduced", type=bool, action=argparse.BooleanOptionalAction,
                        default=False,
                        help="Use reduced benchmark set (default: False)")
    return parser.parse_args()


def main():
    args = parse_and_validate_args()
    benchmark_cfg_file = "scripts/specs_reduced.yaml" if args.reduced else "scripts/specs.yaml"
    benchmark_cfg = read_yaml_cfg(benchmark_cfg_file)["HeCBench"]
    requested_system = args.system
    compiled_any = False
    skipped = []
    failed = []

    for bench, bench_cfg in benchmark_cfg.items():
        system_dict = bench_cfg.get("systems", {})

        if requested_system not in system_dict:
            skipped.append(bench)
            continue

        cfgs = system_dict[requested_system]

        # Safer than eval() for YAML strings representing Python literals (lists/strings)
        compile_flags = ast.literal_eval(cfgs["compilation_flags"])

        print(f"{args.action.capitalize()}ing {bench}-{requested_system}")
        benchmark_folder = os.path.join(args.hecbench_dir, "src", f"{bench}-sycl")

        make_command = (["make"] + list(compile_flags)) if args.action == "build" else ["make", "clean"]
        status_code = subprocess.call(args=make_command, cwd=benchmark_folder)
        if status_code:
            raise ChildProcessError(f"Failed {args.action}ing {bench}-{requested_system}.")

        compiled_any = True

        app_command = ast.literal_eval(bench_cfg.get("run_command", [""]))
        if args.test and args.action == "build":
            print(f"Testing {bench}-{requested_system} with command: {' '.join(app_command)}")
            test_status_code = subprocess.call(args=app_command, cwd=benchmark_folder)
            if test_status_code:
                print(f"ERROR: Failed testing {bench}-{requested_system}.")
                failed.append(bench)

    if not compiled_any:
        raise ValueError(
            f"GPU System '{requested_system}' was not found for any benchmark in {benchmark_cfg_file}. "
            f"Valid values are: intel, amd, nvidia."
        )

    if skipped:
        print(f"Skipped {len(skipped)} benchmarks (no '{requested_system}' variant): {', '.join(skipped)}")

    if failed:
        print(f"Failed {len(failed)} benchmarks: {', '.join(failed)}")

if __name__ == "__main__":
    main()