#!/usr/bin/env python3

import os
import argparse
from typing import Tuple
import pickle

from common import read_yaml_cfg, capture_subprocess_output


RESULT_PKLE_FILE_NAME = "amd-full-opcode-histogram-results.pkl"


def parse_and_validate_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("Instruction count runner script")
    parser.add_argument(
        "--hecbench_dir",
        type=str,
        default="/work/HeCBench",
        help="location of the HeCBench repo",
    )
    parser.add_argument(
        "--luthier_opcode_histogram_tool_path", type=str,
        default="Luthier/build/examples/OpcodeHistogram/libLuthierOpcodeHistogram.so",
        help="location of the luthier instruction count tool",
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


def luthier_get_instr_count_tool_results(
    stdout: str,
    stderr: str,
    tool_run: bool = True,
    instrumented: bool = True,
) -> Tuple[int, int]:
    combined = stdout + "\n" + stderr
    lines = combined.splitlines()

    instruction_count = -1
    luthier_kernel_time = -1

    for line in reversed(lines):
        if tool_run and not instrumented:
            if luthier_kernel_time != -1:
                break
        elif tool_run and instrumented:
            if (
                instruction_count != -1
                and luthier_kernel_time != -1
            ):
                break

        if "Total number of instructions counted:" in line:
            instruction_count = int(
                line.replace("Total number of instructions counted:", "")
                    .replace(".", "")
                    .strip()
            )
            continue

        if "Total kernel run time (us):" in line:
            luthier_kernel_time = int(
                line.replace("Total kernel run time (us):", "")
                    .replace(".", "")
                    .strip()
            )
            continue

    if tool_run and luthier_kernel_time == -1:
        raise EOFError(
            "Failed to find the Luthier kernel time (Total kernel run time (us) line)."
        )

    if tool_run and instrumented and instruction_count == -1:
        raise EOFError("Failed to find the instruction count.")

    return instruction_count, luthier_kernel_time


def main():
    args = parse_and_validate_args()
    benchmark_cfg = read_yaml_cfg(args.specs_yaml)
    programming_model = "sycl-amd"

    for bench in benchmark_cfg["Opcode"]["benchmarks"]:
        out = {}

        cfgs = benchmark_cfg["HeCBench"][bench]["programming_models"][programming_model]
        run_flags = eval(cfgs["run_command"])  # assumed trusted YAML

        benchmark_folder = os.path.join(
            args.hecbench_dir, "src", f"{bench}-sycl"
        )

        result_path = os.path.join(benchmark_folder, RESULT_PKLE_FILE_NAME)
        if os.path.exists(result_path) and not args.overwrite_results:
            print(f"Skipping {bench}-sycl (results already exist).")
            continue

        # ------------------------------------------------------------------
        # Instrumented run
        # ------------------------------------------------------------------
        env_vars = os.environ.copy()
        env_vars["LD_PRELOAD"] = os.path.abspath(args.luthier_opcode_histogram_tool_path)
        env_vars["HIP_ENABLE_DEFERRED_LOADING"] = "0"

        print(
            f"Running instrumented {bench}-sycl: {' '.join(run_flags)}"
        )

        rc, stdout, stderr = capture_subprocess_output(
            args=run_flags,
            cwd=benchmark_folder,
            env=env_vars,
            dump_stdout_stderr=args.dump_stdout_stderr,
        )
        if rc:
            raise ChildProcessError("Instrumented run failed.")

        instr_cnt, luthier_runtime = (
            luthier_get_instr_count_tool_results(stdout, stderr, True, True)
        )

        out["Number of Instructions"] = instr_cnt
        out["Instrumented Luthier Kernel Runtime (us)"] = luthier_runtime

        # ------------------------------------------------------------------
        # Un-instrumented with Luthier framework
        # ------------------------------------------------------------------
        env_vars["LUTHIER_ARGS"] = "--instr-end-interval=0"

        print(
            f"Running un-instrumented with Luthier framework "
            f"{bench}-sycl"
        )

        rc, stdout, stderr = capture_subprocess_output(
            args=run_flags,
            cwd=benchmark_folder,
            env=env_vars,
            dump_stdout_stderr=args.dump_stdout_stderr,
        )
        if rc:
            raise ChildProcessError(
                "Un-instrumented with Luthier framework run failed."
            )

        _, luthier_runtime = (
            luthier_get_instr_count_tool_results(stdout, stderr, True, False)
        )

        out[
            "Un-instrumented with Luthier-framework, Luthier Kernel Runtime (us)"
        ] = luthier_runtime

        print(out)

        with open(result_path, "wb") as f:
            pickle.dump(out, f, protocol=pickle.HIGHEST_PROTOCOL)

        print(f"Ran {bench} benchmarks.")


if __name__ == "__main__":
    main()