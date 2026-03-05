import os
import argparse
import subprocess
from typing import Tuple
import pickle
from contextlib import contextmanager

RESULT_PKLE_FILE_NAME = "detect-memory-race-model-results.pkl"


def capture_subprocess_output(cmd, shell=False, cwd=None):
    result = subprocess.run(cmd, shell=shell, cwd=cwd,
                          capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def parse_and_validate_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("Memory cache model running script")
    parser.add_argument(
        "--kit",
        type=str,
        default=".",
        help="Full path of the GTPin kit",
    )
    parser.add_argument(
        "--app", type=str,
        default=".",
        help="Full path of the compiled race_condition application",
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

def get_race_condition_count_tool_results(
    stdout: str,
    stderr: str,
) -> Tuple[int]:
    combined = stdout + "\n" + stderr
    lines = combined.splitlines()

    total_race_detected = -1

    for line in reversed(lines):
        if "Total Race conditions detected   =" in line:
            total_race_detected = int(
                line.replace("Total Race conditions detected   =", "").strip()
            )
            continue

    if total_race_detected == -1:
        raise EOFError(
            "Failed to find the results of cache model profiling."
        )

    return total_race_detected


def main():
    args        = parse_and_validate_args()
    gtpin       = os.path.join(args.kit, "Profilers", "Bin", "gtpin")
    app_folder  = os.path.join(args.app)
    result_path = os.path.join(app_folder, RESULT_PKLE_FILE_NAME)

    pickl_file = open(result_path, "wb")

    # Usage
    with change_dir(app_folder):
        out = {}

        cmd = [gtpin,
               "-t",
               "cachelineprof",
               "--mode",
               "5",
               "--",
               "race_condition"]

        # ------------------------------------------------------------------
        # Run profiling
        # ------------------------------------------------------------------
        print("Running: {}".format(' '.join(cmd)))

        rc, stdout, stderr = capture_subprocess_output(cmd=cmd, cwd=app_folder)
        if rc:
            raise ChildProcessError("Profiling run failed. rc = {}".format(rc))

        race_condition_count  = get_race_condition_count_tool_results(stdout, stderr)
        out["cmd"]                         = "{}".format(' '.join(cmd))
        out["Number of detected races"]    = race_condition_count

        pickle.dump(out, pickl_file, protocol=pickle.HIGHEST_PROTOCOL)

        cmd = [gtpin,
               "-t",
               "cachelineprof",
               "--mode",
               "5",
               "--",
               "race_condition",
               "--no_race"]

        print("Running: {}".format(' '.join(cmd)))
        rc, stdout, stderr = capture_subprocess_output(cmd=cmd, cwd=app_folder)
        if rc:
            raise ChildProcessError("Profiling run failed. rc = {}".format(rc))

        race_condition_count  = get_race_condition_count_tool_results(stdout, stderr)
        out["cmd"]                         = "{}".format(' '.join(cmd))
        out["Number of detected races"]    = race_condition_count

        pickle.dump(out, pickl_file, protocol=pickle.HIGHEST_PROTOCOL)

        pickl_file.close()
        print("FINISHED")


if __name__ == "__main__":
    main()