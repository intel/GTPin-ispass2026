# Artifact for ISPASS 2026 Paper "GTPin: Enhancing Intel&reg; GPU Profiling With High-Level Binary Instrumentation"

This repository contains the artifact for the paper
"GTPin: Enhancing Intel&reg; GPU Profiling With High-Level Binary Instrumentation" accepted to 2026 IEEE International Symposium
on Performance Analysis of Systems and Software (ISPASS '26).
Some measurements in this work build upon the [luthier-ispass2025](https://github.com/NUCAR-DEV/luthier-ispass2025) artifact, and parts of its content have been reused here.

## Contents
1. A snapshot of the [Luthier project](https://github.com/matinraayai/Luthier) under the
   [`Luthier/`](./Luthier) folder, with git revision number `6a1ae19b62ea9d4b021e4555c55a02b5bd1a885a`.
2. Fifteen benchmarks from the [HeCBench repository](https://github.com/zjin-lcf/HeCBench) are cloned at setup
   time into the [`HeCBench/`](./HeCBench) folder at git revision
   `b59cdcc3755c3a0cd39b4b9925ac5aa76b1d1171` (not shipped in the repo — see [Setup](#setup) below).
3. `race_condition` workload under the [`GTPin/race_condition`](./GTPin/race_condition) folder.
4. `ze_gemm` workload cloned from [PTI-GPU](https://github.com/intel/pti-gpu) at setup time into the [`pti-gpu`](./pti-gpu) folder.
5. [NVBit](https://github.com/NVlabs/NVBit) version 1.7.4 is downloaded at setup time into the
   [`nvbit_release/`](./nvbit_release) folder (not shipped in the repo — see [Setup](#setup) below).
   The opcode histogram tool has been modified to measure the host runtime of the instrumented
   kernels; the patched source is stored in [`nvbit_patches/`](./nvbit_patches).
6. A [GTPin](https://www.intel.com/content/www/us/en/developer/articles/tool/gtpin.html) Kit version 4.7.1 downloaded during setup into [`GTPin/Profilers`](./GTPin/Profilers) folder.
7. Patched GTPin tool sources under [`GTPin/OpcodeprofFiles`](./GTPin/OpcodeprofFiles) folder.
8. A set of Python scripts under [`scripts/`](./scripts) used to set up external dependencies,
   run the experiments, and obtain the results shown in the figures in text format.

## Requirements
The experiments were performed on the three following systems:
1. Intel&reg; GPU for GTPin experiments and performance measurements:
Intel&reg; Core&trade; Ultra processor with Arc&trade; integrated GPU
2. AMD&reg; GPU for Luthier performance measurements:
AMD&reg; EPYC&trade; 7313 16-Core Processor with an AMD
Instinct&trade; MI250 GPU
3. NVIDIA&reg; GPU for NVBit performance measurements:
Intel&reg; Xeon&trade; Platinum 8480+ with NVIDIA&reg; A100
80GB PCIe

### Intel&reg; system:

**Hardware requirements:**
1. CPU/GPU: Intel&reg; Core&trade; Ultra 5 125H processor with Intel&reg; Arc&trade; Graphics (codenamed Meteor Lake-P)

**Software requirements:**
1. A Linux OS (Ubuntu 22.04.5 LTS was used).
2. Intel&reg; GPU Driver with compute packages (v26.05.37020.3 was used).
3. Intel&reg; oneAPI C++ Essentials (v2025.2 was used).
4. OpenCL header packages.
5. GNU C/C++ Compiler version 12.
6. Python 3 with packages `cxxheaderparser`, `pcpp`, and `yacs`.
7. CMake version 3.28.3.

### AMD&reg; system:

**Hardware requirements:**
1. GPU: AMD&reg; Instinct MI250
2. CPU: AMD&reg; EPYC 7313 16-Core

**Software requirements:**
1. A Linux OS (Ubuntu 22.04.5 LTS was used).
2. AMD&reg; GPU Kernel Driver (v6.8.3 was used).
3. [Bleeding-edge ROCm compilation software stack](https://github.com/ROCm/llvm-project) obtained from the
   `amd-staging` branch of the LLVM ROCm fork.
4. GNU C/C++ Compiler version 12.
5. Python 3 with packages `cxxheaderparser`, `pcpp`, and `yacs`.
6. CMake version 3.28.3.

### NVIDIA&reg; system:

**Hardware requirements:**
1. GPU: NVIDIA&reg; A100 80GB PCIe
2. CPU: Intel&reg; Xeon&trade; Platinum 8480+ (Sapphire Rapids)

**Software requirements:**
1. A Linux OS (Ubuntu 22.04.5 LTS was used).
2. NVIDIA&reg; Kernel Driver (v580.126.09 was used).
3. NVIDIA&reg; CUDA toolkit version 12.8.0.
4. Intel&reg; LLVM DPC++ compiler v20.0 with NVIDIA&reg; CUDA backend support.
5. GNU C/C++ Compiler version 12.
6. Python 3 with packages `cxxheaderparser`, `pcpp`, and `yacs`.
7. CMake version 3.28.3.

## How To Run

1. Clone this repository, and change to the repository directory:
   ```bash
   git clone --single-branch --depth 1 https://github.com/intel/GTPin-ispass2026
   cd GTPin-ispass2026
   ```

### Setup

2. **Clone PTI-GPU** — repository for Level Zero samples:
   ```bash
   git clone https://github.com/intel/pti-gpu
   ```
3. **Set up HeCBench** — this sparse-clones the 15 benchmarks used in this artifact:
   ```bash
   python3 scripts/setup_hecbench.py
   ```
4. **Set up NVBit** — this downloads NVBit v1.7.4 and applies the patched opcode histogram tool:
   ```bash
   python3 scripts/setup_nvbit.py
   ```

### Build Tools
5. Install the software dependencies based on the system you measure.
   For detailed instructions on Intel&reg; system setup, see [GTPin/README.md](./GTPin/README.md).

6. According to the system, build the instrumentation tools, assuming the [Setup](#setup) stage has been completed.

   For AMD&reg;, follow the detailed instructions in [`Luthier/`](./Luthier).
   For NVIDIA&reg;, follow the detailed instructions in [`nvbit_release/`](./nvbit_release).
   For detailed instructions on GTPin setup, see [GTPin/README.md](./GTPin/README.md).

### Build & Run Benchmarks

For reproduction of Fig. 3 and Fig. 4, please follow the instructions in [GTPin/REPRODUCE34.md](./GTPin/REPRODUCE34.md).

The following are the instructions for reproducing Fig. 5:

#### Intel
7. Clean, build, and test the HeCBench benchmarks:
   ```bash
   source /opt/intel/oneapi/setvars.sh
   python3 scripts/compile_benchmarks.py --action clean
   python3 scripts/compile_benchmarks.py --action build --test --reduced --system intel
   ```

8. To run the experiments, run the following script:
   ```bash
   python3 scripts/intel_opcodeprof.py --dump_stdout_stderr
   ```
   Note that `--dump_stdout_stderr` dumps the output of each experiment to standard output/error, which
   can be quite large; therefore, it is recommended to limit the terminal scrollback when running the experiments.

9. To create a CSV file with the results, run the following script:
   ```bash
   python3 scripts/intel_print_opcodeprof.py
   ```
#### AMD

7. Clean, build, and test the HeCBench benchmarks:
   ```bash
   python3 scripts/compile_benchmarks.py --action clean
   python3 scripts/compile_benchmarks.py --action build --test --reduced --system amd
   ```

8. To run the experiments, run the following script:
   ```bash
   python3 scripts/amd_opcode_histogram.py --dump_stdout_stderr
   ```
   Note that `--dump_stdout_stderr` dumps the output of each experiment to standard output/error, which
   can be quite large; therefore, it is recommended to limit the terminal scrollback when running the experiments.

9. To create a CSV file with the results, run the following script:
   ```bash
   python3 scripts/amd_print_opcode_histogram.py
   ```

#### NVIDIA

7. Clean, build, and test the HeCBench benchmarks:
   ```bash
   python3 scripts/compile_benchmarks.py --action clean
   python3 scripts/compile_benchmarks.py --action build --test --reduced --system nvidia
   ```

8. To run the experiments, run the following script:
   ```bash
   python3 scripts/nvidia_opcode_hist.py --dump_stdout_stderr
   ```
   Note that `--dump_stdout_stderr` dumps the output of each experiment to standard output/error, which
   can be quite large; therefore, it is recommended to limit the terminal scrollback when running the experiments.

9. To create a CSV file with the results, run the following script:
   ```bash
   python3 scripts/nvidia_print_opcode_hist.py
   ```
