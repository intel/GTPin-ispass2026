# Reproducing GPU Memory Profiling from Section III

This guide explains how to reproduce the GPU memory profiling modes described in Sections III-A and III-B from the GTPin-ispass2026 paper on an Intel&reg; GPU system.

To evaluate GTPin beyond reproducing the results described in this artifact, please refer to the [`GTPin User Guide`](https://software.intel.com/sites/landingpage/gtpin/index.html).

## Prerequisites
It is assumed you followed the instructions from the [`How To Run`](../README.md#how-to-run) section in the GTPin-ispass2026/README.md up to number 6

NOTE: Make sure you are running in an environment *WITHOUT* oneAPI loaded

## Section III-A: Modelling a direct mapped cache (Fig. 3)
For this test we use the ze_gemm sample application
### Setup
Starting from the GTPin-ispass2026 folder
```bash
cd ./pti-gpu/samples/ze_gemm/
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
make
./ze_gemm
```

### Run
Starting from the GTPin-ispass2026 folder
```bash
python3 ./scripts/intel_memory_cache_model.py
python3 ./scripts/intel_print_memory_cache_model.py
```

## Section III-B: Detecting race condition
For this test we use an application that simulates memory race conditions

### Setup
Starting from the GTPin-ispass2026 folder

```bash
cd ./GTPin/race_condition
make clean
make
```
### Run
Starting from the GTPin-ispass2026 folder
```bash
python3 ./scripts/intel_detect_race_condition.py
python3 ./scripts/intel_print_detect_race_condition.py
```
