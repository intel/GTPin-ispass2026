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

import os
import argparse
import subprocess
from typing import Tuple
import pickle
from contextlib import contextmanager

RESULT_PKLE_FILE_NAME = "memory-cache-model-results.pkl"

CACHE_SIZE_KB = ['64', '16', '4', '1']
CACHELINE_SIZE_BYTE = ['64', '32', '16', '8', '4', '2', '1']

def capture_subprocess_output(cmd, shell=False, cwd=None):
    result = subprocess.run(cmd, shell=shell, cwd=cwd,
                          capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def parse_and_validate_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("Memory cache model running script")
    parser.add_argument(
        "--kit",
        type=str,
        default="./GTPin",
        help="Full path of the GTPin kit",
    )
    parser.add_argument(
        "--app", type=str,
        default="./pti-gpu/samples/ze_gemm/build",
        help="Full path of the compiled ze_gemm application",
    )

    return parser.parse_args()

@contextmanager
def change_dir(destination):
    """Context manager to change directory and return to original"""
    original_dir = os.getcwd()
    try:
        os.chdir(destination)
        yield
    finally:
        os.chdir(original_dir)

def get_hits_misses_count_tool_results(
    stdout: str,
    stderr: str,
) -> Tuple[int, int]:
    combined = stdout + "\n" + stderr
    lines = combined.splitlines()

    hits_count = -1
    misses_count = -1

    for line in reversed(lines):
        if "Total cache hits   =" in line:
            hits_count = int(
                line.replace("Total cache hits   =", "").strip()
            )
            continue

        if "Total cache misses =" in line:
            misses_count = int(
                line.replace("Total cache misses =", "").strip()
            )
            continue

    if hits_count and misses_count == -1:
        raise EOFError(
            "Failed to find the results of cache model profiling."
        )

    return hits_count, misses_count


def main():
    args           = parse_and_validate_args()
    gtpin          = os.path.realpath(os.path.join(args.kit, "Profilers", "Bin", "gtpin"))
    ze_gemm_folder = os.path.realpath(os.path.join(args.app))
    result_path    = os.path.join(ze_gemm_folder, RESULT_PKLE_FILE_NAME)

    if not os.path.isfile(gtpin):
        raise FileNotFoundError(
            f"Could not find GTPin profiler at {gtpin}. Please check the path and try again."
        )

    pickl_file = open(result_path, "wb")

    # Usage
    with change_dir(ze_gemm_folder):
        for cache_size in CACHE_SIZE_KB:
            for cacheline_size in CACHELINE_SIZE_BYTE:
                out = {}

                cmd = [gtpin,
                       "-t",
                       "cachelineprof",
                       "--mode",
                       "3",
                       "--cache_size",
                       cache_size,
                       "--cacheline_size",
                       cacheline_size,
                       "--",
                       "ze_gemm",
                       "256",
                       "1"]

                # ------------------------------------------------------------------
                # Run profiling
                # ------------------------------------------------------------------
                print("Running: {}".format(' '.join(cmd)))

                rc, stdout, stderr = capture_subprocess_output(cmd=cmd)
                if rc:
                    raise ChildProcessError("Profiling run failed. rc = {}".format(rc))

                hits_count, misses_count = get_hits_misses_count_tool_results(stdout, stderr)
                out["cmd"]                         = "{}".format(' '.join(cmd))
                out["Cache size (in KB)"]          = cache_size
                out["Cacheline size (in Byte)"]    = cacheline_size
                out["Number of hits"]              = hits_count
                out["Number of misses"]            = misses_count
                out["Number of cacheline acceses"] = hits_count + misses_count
                out["Hits distribution(%)"]        = int(100 * float(hits_count) / float(hits_count + misses_count))
                out["Misses distribution(%)"]      = 100 - int(100 * float(hits_count) / float(hits_count + misses_count))

                pickle.dump(out, pickl_file, protocol=pickle.HIGHEST_PROTOCOL)

        pickl_file.close()
        print("FINISHED")


if __name__ == "__main__":
    main()