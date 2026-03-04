# Artifact for ISPASS 2026 Paper "GTPin: Enhancing Intel GPU Profiling With High-Level Binary Instrumentation"

This repository contains the artifact for the paper
"GTPin: Enhancing Intel GPU Profiling With High-Level Binary Instrumentation" accepted to 2026 IEEE International Symposium 
on Performance Analysis of Systems and Software (ISPASS '26).

## Contents
1. A snapshot of the [Luthier project](https://github.com/matinraayai/Luthier) under the 
   [`Luthier/`](./Luthier) folder, with git revision number `6a1ae19b62ea9d4b021e4555c55a02b5bd1a885a`.
2. A snapshot of the [HeCBench repository](https://github.com/zjin-lcf/HeCBench) used to obtain the figures in 
   the paper under the [`HecBench`](./HeCBench) folder, with git revision 
   number `b59cdcc3755c3a0cd39b4b9925ac5aa76b1d1171`.
4. A snapshot of [NVBit](https://github.com/NVlabs/NVBit) version 1.7.4, under the [`nvbit_release`](./nvbit_release)
   folder. The instruction counter example tool has been modified to measure the host runtime of the instrumented 
   kernels.
5. A GTPin Kit TBD
6. A set of Python scripts used to run the experiments and obtain the results shown in the figures in text format.

## Requirements
TBD
1. An NVIDIA V100 and an AMD MI100 GPU attached to the same system.
2. NVIDIA Kernel Driver (v560.35.03 was used).
3. NVIDIA Container toolkit (v1.16.2 was used).
4. AMDGPU Kernel Driver (v.6.2.3 was used).
5. A Linux OS (Ubuntu 22.04.5 LTS was used).

The container itself contains the following pre-requisite software:
TBD not container
1. NVIDIA CUDA toolkit version 12.8.0.
2. GNU C/C++ Compiler version 12.
3. Python 3 with packages `cxxheaderparser`, `pcpp`, and `yacs`.
4. CMake version 3.28.3.
5. [Bleeding-edge ROCm compilation software stack](https://github.com/ROCm/llvm-project) obtained by from the 
   `amd-staging` branch of the LLVM ROCm fork.
6. [Intel SYCL compiler](https://github.com/intel/llvm).


## How To Run


# ISPASS 2026 GTPin Artifact – Environment & Execution Guide

This document describes how to set up and run the ISPASS 2026 GTPin artifact on Intel ORTCE infrastructure for both **AMD MI250** and **NVIDIA A100** platforms.

---

## Prerequisites

### Intel ORTCE Environment
- **Required permissions**:
  - `sudo`
  - `debug`
- **Target machines**:
  - `ortce-amdgpu-mi250`
  - `ortce-a100-80G1`

---

## Connecting to ORTCE

### Login to ORTCE Lab
```bash
ssh rburstei@ortce-skl.jf.intel.com
```

---

## AMD MI250 Setup

### Connect to AMD MI250 Node
```bash
srun -w ortce-amdgpu-mi250 --pty bash
```

### Long Runs (Debug Queue)
For long executions, use the debug queue (requires re-approval):
```bash
srun -p debug --qos=debug -w ortce-amdgpu-mi250 --time=2000 --pty /bin/bash
```

---

### Repository Setup
Clone the repository or move to your existing environment:
```bash
cd /nfs/pdx/home/rburstei/gtpin/gtpin-ispass2026/
```

---

### Run Docker Container (AMD)

> **Note:** `sudo` permissions are required.

```bash
sudo docker run --rm -it   -v $PWD:/work/   --device=/dev/kfd   --device=/dev/dri/   --privileged   --security-opt seccomp=unconfined   --shm-size=16G   --cap-add=SYS_PTRACE   --ipc=host   intel-gtpin-ispass-2026-artifact   /bin/bash
```

Alternative container image:
```bash
sudo docker run --rm -it   -v $PWD:/work/   --device=/dev/kfd   --device=/dev/dri/   --privileged   --security-opt seccomp=unconfined   --shm-size=16G   --cap-add=SYS_PTRACE   --ipc=host   containers.rc.northeastern.edu/luthier/ispass-2025-artifact   /bin/bash
```

---

### Build SYCL Applications (AMD Only)
If required:
```bash
python3 scripts/compile_benchmarks.py --action clean
```

---

### Run Experiments (AMD)

Default run:
```bash
python3 scripts/amd_opcode_histogram.py --dump_stdout_stderr
```

Reduced specification set:
```bash
python3 scripts/amd_opcode_histogram.py --dump_stdout_stderr --specs_yaml scripts/specs_reduced.yaml
```

---

## NVIDIA A100 Setup

### Connect to NVIDIA A100 Node
```bash
srun -w ortce-a100-80G1 --pty bash
```

### Long Runs (Debug Queue)
```bash
srun -p debug --qos=debug -w ortce-a100-80G1 --time=2000 --pty /bin/bash
```

---

### Run Docker Container (NVIDIA)

```bash
docker run --gpus all -it   -v $(pwd):/work   containers.rc.northeastern.edu/luthier/ispass-2025-artifact:latest
```

---

## Notes
- Ensure you are running on the correct node (AMD vs. NVIDIA) before launching Docker.
- Debug queue usage may require prior approval.
- Paths and permissions assume Intel ORTCE infrastructure.

---
