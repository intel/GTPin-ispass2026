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
        default="/work/HeCBench",
        help="location of the HeCBench repo",
    )
    parser.add_argument(
        "--gtpin_profiler_path",
        type=str,
        default="/work/GTPin_Release/Profilers",
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
    sycl_kernel_runtime = -1     # us (converted from ms)
    gtpin_kernel_time = -1     # us (converted from sec)

    sycl_ms_re = re.compile(
        r"SYCL_MEASUREMENT:\s*Total kernel execution time on GPU:\s*([0-9]*\.?[0-9]+)\s*\(ms\)"
    )

    for line in reversed(lines):
        if not tool_run and not instrumented:
            if sycl_kernel_runtime != -1:
                break
        elif tool_run and not instrumented:
            if sycl_kernel_runtime != -1 and gtpin_kernel_time != -1:
                break
        elif tool_run and instrumented:
            if (
                instruction_count != -1
                and sycl_kernel_runtime != -1
                and gtpin_kernel_time != -1
            ):
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

        m = sycl_ms_re.search(line)
        if m:
            sycl_kernel_runtime = int(round(float(m.group(1)) * 1000.0))
            continue

    if sycl_kernel_runtime == -1:
        print("Warning: Failed to find the kernel runtime (SYCL_MEASUREMENT line). Setting to -1.")
    if tool_run and gtpin_kernel_time == -1:
        print("Warning: Failed to find the GTPin kernel time (Total kernel run time (sec) line). Setting to -1.")

    if tool_run and instrumented and instruction_count == -1:
        print("Warning: Failed to find the instruction count. Setting to -1.")

    return instruction_count, sycl_kernel_runtime, gtpin_kernel_time


def main():
    args = parse_and_validate_args()
    benchmark_cfg = read_yaml_cfg(args.specs_yaml)
    gtpin_exe_path = os.path.join(args.gtpin_profiler_path, "Bin", "gtpin")
    tools_path = os.path.join(args.gtpin_profiler_path, "Examples", "build")
    instrument_per_ins_knob = "--instrument_per_ins"

    for bench in benchmark_cfg["Opcode"]["benchmarks"]:
        programming_model = "sycl-intel"
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
        # Un-instrumented run
        # ------------------------------------------------------------------
        env_vars = os.environ.copy()
        print(
            f"Running un-instrumented {bench}-sycl: {' '.join(run_flags)}"
        )

        rc, stdout, stderr = capture_subprocess_output(
            args=run_flags,
            cwd=benchmark_folder,
            env=env_vars,
            dump_stdout_stderr=args.dump_stdout_stderr,
        )
        if rc and bench != "hmm":
            raise ChildProcessError("Un-instrumented run failed.")

        _, sycl_runtime, _ = gtpin_get_opcodeprof_tool_results(
            stdout, stderr, tool_run=False, instrumented=False
        )
        out["Un-instrumented SYCL Kernel Runtime (us)"] = sycl_runtime

        # ------------------------------------------------------------------
        # Instrumented run - LLI Opcodeprof
        # ------------------------------------------------------------------
        # Run with GTPin framework with instrumentation per instruction
        tool_path = os.path.join(tools_path, "opcodeprof.so")
        gtpin_instrumented_run_flags = [gtpin_exe_path, "-t", tool_path, instrument_per_ins_knob, "--"] + list(run_flags)
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
            raise ChildProcessError("Instrumented run failed.")

        instr_cnt, sycl_runtime, gtpin_runtime = (
            gtpin_get_opcodeprof_tool_results(stdout, stderr, True, True)
        )

        out["Number of Instructions - LLI Opcodeprof"] = instr_cnt
        out["Instrumented SYCL Kernel Runtime - LLI Opcodeprof (us)"] = sycl_runtime
        out["Instrumented GTPin Kernel Runtime - LLI Opcodeprof (us)"] = gtpin_runtime

        # ------------------------------------------------------------------
        # Instrumented run - HLI Opcodeprof
        # ------------------------------------------------------------------
        # Run with GTPin framework with instrumentation per instruction
        tool_path = os.path.join(tools_path, "hlif_opcodeprof.so")
        gtpin_instrumented_run_flags = [gtpin_exe_path, "-t", tool_path, instrument_per_ins_knob, "--"] + list(run_flags)
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
            raise ChildProcessError("Instrumented run failed.")

        instr_cnt, sycl_runtime, gtpin_runtime = (
            gtpin_get_opcodeprof_tool_results(stdout, stderr, True, True)
        )

        out["Number of Instructions - HLI Opcodeprof"] = instr_cnt
        out["Instrumented SYCL Kernel Runtime - HLI Opcodeprof (us)"] = sycl_runtime
        out["Instrumented GTPin Kernel Runtime - HLI Opcodeprof (us)"] = gtpin_runtime

        # ------------------------------------------------------------------
        # Un-instrumented with GTPin framework
        # ------------------------------------------------------------------
        # Run with GTPin framework but execute original module (no instrumentation)
        gtpin_uninstrumented_run_flags = [gtpin_exe_path, "-t", tool_path, "--run_original_module", "--"] + list(run_flags)

        print(
            f"Running un-instrumented with GTPin framework "
            f"{bench}-sycl"
        )

        rc, stdout, stderr = capture_subprocess_output(
            args=gtpin_uninstrumented_run_flags,
            cwd=benchmark_folder,
            env=env_vars,
            dump_stdout_stderr=args.dump_stdout_stderr,
        )
        if rc and bench != "hmm":
            raise ChildProcessError(
                "Un-instrumented with GTPin framework run failed."
            )

        _, sycl_runtime, gtpin_runtime = (
            gtpin_get_opcodeprof_tool_results(stdout, stderr, True, False)
        )

        out[
            "Un-instrumented with GTPin-framework, SYCL Kernel Runtime (us)"
        ] = sycl_runtime
        out[
            "Un-instrumented with GTPin-framework, GTPin Kernel Runtime (us)"
        ] = gtpin_runtime

        print(out)

        with open(result_path, "wb") as f:
            pickle.dump(out, f, protocol=pickle.HIGHEST_PROTOCOL)

        print(f"Ran {bench} benchmarks.")


if __name__ == "__main__":
    main()
