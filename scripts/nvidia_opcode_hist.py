#!/usr/bin/env python3

import os
import argparse
from typing import Tuple
import pickle

from common import read_yaml_cfg, capture_subprocess_output


RESULT_PKLE_FILE_NAME = "nvidia-full-opcode-hist-results.pkl"


def parse_and_validate_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("Instruction count runner script")
    parser.add_argument(
        "--hecbench_dir",
        type=str,
        default="/work/HeCBench",
        help="location of the HeCBench repo",
    )
    parser.add_argument(
        "--nvbit_opcode_hist_tool_path",
        type=str,
        default="/work/nvbit_release/tools/opcode_hist/opcode_hist.so",
        help="location of the nvbit opcode hist tool",
    )
    parser.add_argument(
        "--dump_stdout_stderr",
        action="store_true",
        help="dump the stdout and stderr of each experiment to screen",
    )
    parser.add_argument(
        "--overwrite_results",
        action="store_true",
        help="overwrite results of benchmarks from a previous run",
    )
    parser.add_argument(
        "--specs_yaml",
        type=str,
        default="scripts/specs.yaml",
        help="location of specs file",
    )

    return parser.parse_args()


def nvbit_get_tool_results(
    stdout: str,
    stderr: str,
    tool_run: bool = True,
    instrumented: bool = True,
) -> Tuple[int, int]:
    combined = stdout + "\n" + stderr
    lines = combined.splitlines()

    instruction_count = -1
    nvbit_kernel_time = -1

    for line in reversed(lines):
        if tool_run and not instrumented:
            if nvbit_kernel_time != -1:
                break
        elif tool_run and instrumented:
            if (
                instruction_count != -1
                and nvbit_kernel_time != -1
            ):
                break

        if "Total app instructions:" in line:
            instruction_count = int(
                line.replace("Total app instructions:", "")
                    .replace(".", "")
                    .strip()
            )
            continue

        if "Total kernel time:" in line:
            nvbit_kernel_time = int(
                line.replace("Total kernel time:", "")
                    .replace(".", "")
                    .strip()
            )
            continue

    if tool_run and nvbit_kernel_time == -1:
        raise EOFError(
            "Failed to find the NVBIT kernel time (Total kernel run time (us) line)."
        )

    if tool_run and instrumented and instruction_count == -1:
        raise EOFError("Failed to find the instruction count.")

    return instruction_count, nvbit_kernel_time


def main():
    args = parse_and_validate_args()
    benchmark_cfg = read_yaml_cfg(args.specs_yaml)

    for bench in benchmark_cfg["InstrCount"]["benchmarks"]:
        for programming_model in benchmark_cfg["InstrCount"]["programming_models"]:
            out = {}

            cfgs = benchmark_cfg["HeCBench"][bench]["programming_models"][programming_model]
            run_flags = eval(cfgs["run_command"])  # assumed trusted YAML

            benchmark_folder = os.path.join(
                args.hecbench_dir, "src", f"{bench}-{programming_model}"
            )

            result_path = os.path.join(benchmark_folder, RESULT_PKLE_FILE_NAME)
            if os.path.exists(result_path) and not args.overwrite_results:
                print(f"Skipping {bench}-{programming_model} (results already exist).")
                continue

            # ------------------------------------------------------------------
            # Instrumented run
            # ------------------------------------------------------------------
            env_vars = os.environ.copy()
            env_vars["LD_PRELOAD"] = args.nvbit_opcode_hist_tool_path
            env_vars["COUNT_WARP_LEVEL"] = "0"
            env_vars["MANGLED_NAMES"] = "0"

            print(
                f"Running instrumented {bench}-{programming_model}: {' '.join(run_flags)}"
            )

            rc, stdout, stderr = capture_subprocess_output(
                args=run_flags,
                cwd=benchmark_folder,
                env=env_vars,
                dump_stdout_stderr=args.dump_stdout_stderr,
            )
            if rc:
                raise ChildProcessError("Instrumented run failed.")

            instr_cnt, nvbit_runtime = (
                nvbit_get_tool_results(stdout, stderr, True, True)
            )

            out["Number of Instructions"] = instr_cnt
            out["Instrumented NVBIT Kernel Runtime (us)"] = nvbit_runtime

            # ------------------------------------------------------------------
            # Un-instrumented with NVBIT framework
            # ------------------------------------------------------------------
            env_vars["INSTR_END"] = "0"

            print(
                f"Running un-instrumented with NVBIT framework "
                f"{bench}-{programming_model}"
            )

            rc, stdout, stderr = capture_subprocess_output(
                args=run_flags,
                cwd=benchmark_folder,
                env=env_vars,
                dump_stdout_stderr=args.dump_stdout_stderr,
            )
            if rc:
                raise ChildProcessError(
                    "Un-instrumented with NVBIT framework run failed."
                )

            _, nvbit_runtime = (
                nvbit_get_tool_results(stdout, stderr, True, False)
            )

            out[
                "Un-instrumented with NVBIT-framework, NVBIT Kernel Runtime (us)"
            ] = nvbit_runtime

            print(out)

            with open(result_path, "wb") as f:
                pickle.dump(out, f, protocol=pickle.HIGHEST_PROTOCOL)

        print(f"Ran {bench} benchmarks.")


if __name__ == "__main__":
    main()