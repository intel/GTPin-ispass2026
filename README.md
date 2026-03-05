# Artifact for ISPASS 2026 Paper "GTPin: Enhancing Intel GPU Profiling With High-Level Binary Instrumentation"

This repository contains the artifact for the paper
"GTPin: Enhancing Intel GPU Profiling With High-Level Binary Instrumentation" accepted to 2026 IEEE International Symposium 
on Performance Analysis of Systems and Software (ISPASS '26).
Some measurements in this work build upon the https://github.com/NUCAR-DEV/luthier-ispass2025 artifact, and parts of its content have been reused here.

## Contents
1. A snapshot of the [Luthier project](https://github.com/matinraayai/Luthier) under the 
   [`Luthier/`](./Luthier) folder, with git revision number `6a1ae19b62ea9d4b021e4555c55a02b5bd1a885a`.
2. Fifteen benchmarks from the [HeCBench repository](https://github.com/zjin-lcf/HeCBench) are cloned at setup
   time into the [`HeCBench/`](./HeCBench) folder at git revision 
   `b59cdcc3755c3a0cd39b4b9925ac5aa76b1d1171` (not shipped in the repo — see [Setup](#setup) below).
4. `ze_gemm` and `race_condition` workloads under TBD.
5. [NVBit](https://github.com/NVlabs/NVBit) version 1.7.4 is downloaded at setup time into the
   [`nvbit_release/`](./nvbit_release) folder (not shipped in the repo — see [Setup](#setup) below).
   The opcode histogram tool has been modified to measure the host runtime of the instrumented 
   kernels; the patched source is stored in [`nvbit_patches/`](./nvbit_patches).
6. A GTPin Kit version 4.7 TBD.
7. A set of Python scripts under [`scripts/`](./scripts) used to set up external dependencies,
   run the experiments, and obtain the results shown in the figures in text format.

## Requirements
The experiments on three following systems:
1. Intel GPU for GTPin experiments and performance measurements: TBD
2. AMD GPU for Luthier performance measurements:
AMD EPYC™ 7313 16-Core Processor with an AMD
Instinct™ MI250 GPU
3. NVIDIA GPU for NVBit performance measurements:
Intel® Xeon™ Platinum 8480+ with NVIDIA A100
80GB PCIe

### Intel system:

TBD

### AMD system:

**Hardware requirements:** 
1. GPU: AMD Instinct MI250
2. CPU: AMD EPYC 7313 16-Core

**Sofrware requirements:**
1. A Linux OS (Ubuntu 22.04.5 LTS was used).
2. AMDGPU Kernel Driver (v.6.8.3 was used).
3. [Bleeding-edge ROCm compilation software stack](https://github.com/ROCm/llvm-project) obtained by from the 
   `amd-staging` branch of the LLVM ROCm fork.
4. GNU C/C++ Compiler version 12.
5. Python 3 with packages `cxxheaderparser`, `pcpp`, and `yacs`.
6. CMake version 3.28.3.

### NVIDIA system:

**Hardware requirements:**
1. GPU: NVIDIA A100 80GB PCIe
2. CPU: Intel Xeon Platinum 8480+ (Sapphire Rapids)

**Sofrware requirements:**
1. A Linux OS (Ubuntu 22.04.5 LTS was used) 
2. NVIDIA Kernel Driver (v580.126.09 was used).
3. NVIDIA CUDA toolkit version 12.8.0.
5. Intel LLVM DPC++ compiler v20.0 with NVIDIA CUDA backend support
4. GNU C/C++ Compiler version 12.
5. Python 3 with packages `cxxheaderparser`, `pcpp`, and `yacs`.
6. CMake version 3.28.3.

## How To Run

1. Clone this repository, and change to the repository directory:
   ```bash
   git clone --single-branch --depth 1 https://github.com/intel/GTPin-ispass2026
   cd GTPin-ispass2026
   ```

### Setup

2. **Set up HeCBench** (requires `git`). This sparse-clones the 15 benchmarks used in this artifact:
   ```bash
   python3 scripts/setup_hecbench.py
   ```
3. **Set up NVBit** (NVIDIA system only; requires `wget` or Python 3). This downloads NVBit v1.7.4 and
   applies the patched opcode histogram tool:
   ```bash
   python3 scripts/setup_nvbit.py
   ```

### Build & Run

4. Install the software dependencies based on the system you measure.
5. Build the HeC benchmarks, pass the system you are measuring:
   ```bash
   TBD "system"
   python3 scripts/compile_benchmarks.py --action build --system intel
   OR
   python3 scripts/compile_benchmarks.py --action build --system amd
   OR
   python3 scripts/compile_benchmarks.py --action build --system nvidia
   ```
6. According to the system, build the instrumentation tools TBD
7. To run the experiments, run the following scripts:
   ```bash
   # For figure 3
   TBD
   # For figure 4
   TBD
   # For figure 6
   python3 scripts/gtpin_opcodeprof.py --dump_stdout_stderr
   OR
   python3 scripts/amd_opcode_histogram.py --dump_stdout_stderr
   OR
   python3 scripts/nvidia_opcode_hist.py --dump_stdout_stderr
   ```
   Note that the `--dump_stdout_stderr` dumps the output of each experiments to the standard output/error, which 
   can be quite large; Therefore, it is recommended to clip the terminal emulator output when running the experiments.
8. To create a .csv file with the results, run the following scripts:
   ```bash
   # For figure 3
   TBD
   # For figure 4
   TBD
   # For figure 6
   python3 scripts/gtpin_print_opcodeprof.py
   OR
   python3 scripts/amd_print_opcode_histogram.py
   OR
   python3 scripts/nvidia_print_opcode_hist.py
   ```
