#!/usr/bin/env python3

import os
import argparse
from typing import Tuple
import pickle
import re

from common import read_yaml_cfg, capture_subprocess_output


RESULT_PKLE_FILE_NAME = "intel-full-opcodeprof-results.pkl"


def parse_and_validate_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("Opcodeprof runner script")
    parser.add_argument(
        "--hecbench_dir",
        type=str,
        default="./HeCBench",
        help="location of the HeCBench repo",
    )
    parser.add_argument(
        "--gtpin_profiler_path",
        type=str,
        default="./GTPin/Profilers",
        help="location of the GTPin kit",
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


def gtpin_get_opcodeprof_tool_results(
    stdout: str,
    stderr: str,
    tool_run: bool = True,
    instrumented: bool = True,
) -> Tuple[int, int, int]:
    combined = stdout + "\n" + stderr
    lines = combined.splitlines()

    instruction_count = -1
    gtpin_kernel_time = -1     # us (converted from sec)

    for line in reversed(lines):
        if tool_run and not instrumented:
            if gtpin_kernel_time != -1:
                break
        elif tool_run and instrumented:
            if (
                instruction_count != -1
                and gtpin_kernel_time != -1
            ):
                break
        else:
            break

        if "Total number of counted instructions:" in line:
            instruction_count = int(
                line.replace("Total number of counted instructions:", "")
                    .replace(".", "")
                    .strip()
            )
            continue

        if "Total kernel run time (sec):" in line:
            gtpin_kernel_time_sec = (
                line.replace("Total kernel run time (sec):", "")
                    .strip()
            )
            gtpin_kernel_time = int(round(float(gtpin_kernel_time_sec) * 1000000))  # convert to us
            continue

    if tool_run and gtpin_kernel_time == -1:
        print("Warning: Failed to find the GTPin kernel time (Total kernel run time (sec) line). Setting to -1.")

    if tool_run and instrumented and instruction_count == -1:
        print("Warning: Failed to find the instruction count. Setting to -1.")

    return instruction_count, gtpin_kernel_time


def main():
    args           = parse_and_validate_args()
    benchmark_cfg  = read_yaml_cfg(args.specs_yaml)
    gtpin_exe_path = os.path.realpath(os.path.join(args.gtpin_profiler_path, "Bin", "gtpin"))
    tools_path     = os.path.realpath(os.path.join(args.gtpin_profiler_path, "Examples", "build"))
    instrument_per_ins_knob = "--instrument_per_ins"

    if not os.path.isfile(gtpin_exe_path):
        raise FileNotFoundError(
            f"Could not find GTPin executable at {gtpin_exe_path}. Please check the path and try again."
        )

    for bench in benchmark_cfg["Opcode"]["benchmarks"]:

        out = {}

        run_flags = eval(benchmark_cfg["HeCBench"][bench]["run_command"])  # assumed trusted YAML

        benchmark_folder = os.path.join(
            args.hecbench_dir, "src", f"{bench}-sycl"
        )

        result_path = os.path.join(benchmark_folder, RESULT_PKLE_FILE_NAME)
        if os.path.exists(result_path):
            if not args.overwrite_results:
                print(f"Skipping {bench}-sycl (results already exist).")
                continue
            else:
                os.remove(result_path)

        env_vars = os.environ.copy()

        tool_path = os.path.join(tools_path, "opcodeprof.so")

        # ------------------------------------------------------------------
        # Un-instrumented with GTPin framework
        # ------------------------------------------------------------------
        # Run with GTPin framework but execute original module (no instrumentation)
        gtpin_uninstrumented_run_flags = [gtpin_exe_path, "-t", tool_path, "--run_original_module", "--profile_dir", "GTPIN_NATIVE", "--"] + list(run_flags)

        print(
            f"Running un-instrumented {bench}-sycl: {' '.join(gtpin_uninstrumented_run_flags)}"
        )
        rc, stdout, stderr = capture_subprocess_output(
            args=gtpin_uninstrumented_run_flags,
            cwd=benchmark_folder,
            env=env_vars,
            dump_stdout_stderr=args.dump_stdout_stderr,
        )
        if rc and bench != "hmm":
            print("Un-instrumented run failed.")

        _, app_runtime = gtpin_get_opcodeprof_tool_results(
            stdout, stderr, tool_run=True, instrumented=False
        )
        out["Un-instrumented APP Kernel Runtime (us)"] = app_runtime

        # ------------------------------------------------------------------
        # Instrumented run - LLI Opcodeprof
        # ------------------------------------------------------------------
        # Run with GTPin framework with instrumentation per instruction
        gtpin_instrumented_run_flags = [gtpin_exe_path, "-t", tool_path, instrument_per_ins_knob, "--profile_dir", "GTPIN_LLI_OPCODEPROF", "--"] + list(run_flags)
        print(
            f"Running instrumented {bench}-sycl: {' '.join(gtpin_instrumented_run_flags)}"
        )

        rc, stdout, stderr = capture_subprocess_output(
            args=gtpin_instrumented_run_flags,
            cwd=benchmark_folder,
            env=env_vars,
            dump_stdout_stderr=args.dump_stdout_stderr,
        )
        if rc and bench != "hmm":
            print("Instrumented run failed.")

        instr_cnt, gtpin_runtime = (
            gtpin_get_opcodeprof_tool_results(stdout, stderr, True, True)
        )

        out["Number of Instructions - LLI Opcodeprof"] = instr_cnt
        out["Instrumented GTPin Kernel Runtime - LLI Opcodeprof (us)"] = gtpin_runtime

        # ------------------------------------------------------------------
        # Instrumented run - HLI Opcodeprof
        # ------------------------------------------------------------------
        # Run with GTPin framework with instrumentation per instruction
        tool_path = os.path.join(tools_path, "hlif_opcodeprof.so")
        gtpin_instrumented_run_flags = [gtpin_exe_path, "-t", tool_path, instrument_per_ins_knob, "--profile_dir", "GTPIN_HLI_OPCODEPROF", "--"] + list(run_flags)
        print(
            f"Running instrumented {bench}-sycl: {' '.join(gtpin_instrumented_run_flags)}"
        )

        rc, stdout, stderr = capture_subprocess_output(
            args=gtpin_instrumented_run_flags,
            cwd=benchmark_folder,
            env=env_vars,
            dump_stdout_stderr=args.dump_stdout_stderr,
        )
        if rc and bench != "hmm":
            print("Instrumented run failed.")

        instr_cnt, gtpin_runtime = (
            gtpin_get_opcodeprof_tool_results(stdout, stderr, True, True)
        )

        out["Number of Instructions - HLI Opcodeprof"] = instr_cnt
        out["Instrumented GTPin Kernel Runtime - HLI Opcodeprof (us)"] = gtpin_runtime

        print(out)

        with open(result_path, "wb") as f:
            pickle.dump(out, f, protocol=pickle.HIGHEST_PROTOCOL)

        print(f"Ran {bench} benchmarks.")


if __name__ == "__main__":
    main()
