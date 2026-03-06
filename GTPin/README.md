# Environment Setup Guide

This guide explains how to set up the environment to run the GTPin-ispass2026 scripts on an Intel&reg; GPU system.

## Prerequisites

### System Requirements
1. Ubuntu 24.04 Linux distribution
2. Intel&reg; Core Ultra&trade; processor with Intel&reg; Arc graphics
   (Tested on Intel&reg; Core Ultra&trade; 9 155H processor)


### 1. Install System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y software-properties-common python3-venv python3-full gnupg wget
```

### 2. Install Intel&reg; Graphics Drivers and Level Zero

Add the Intel&reg; graphics PPA and install the required packages:

```bash
sudo add-apt-repository -y ppa:kobuk-team/intel-graphics
sudo apt-get install -y libze-intel-gpu1 libze1 intel-metrics-discovery intel-opencl-icd clinfo intel-gsc
sudo apt-get install -y libze-dev intel-ocloc
```

### 3. Install OpenCL&trade; Development Headers

```bash
sudo apt-get install -y opencl-headers ocl-icd-opencl-dev
```

### 4. Install Intel&reg; oneAPI&trade; CPP Essentials Toolkit (v2025.2)

```bash
wget https://registrationcenter-download.intel.com/akdlm/IRC_NAS/2d607ce3-9aa8-492d-a97d-e473dc37be66/intel-cpp-essentials-2025.2.0.532_offline.sh
sudo mkdir -p /opt/intel/oneapi
sudo ./intel-cpp-essentials-2025.2.0.532_offline.sh -s -a --eula accept --silent --install-dir /opt/intel/oneapi
```

### 5. Reboot
```bash
sudo reboot
```

## GTPin Setup

Starting from the GTPin-ispass2026/GTPin folder

### 1. Download and extract GTPin kit
```bash
wget https://downloadmirror.intel.com/914392/external-release-gtpin-4.7.1-linux.tar.xz
tar -xf ./external-release-gtpin-4.7.1-linux.tar.xz
```

### 2. Build modified GTPin tools
```bash
GTPIN_DIR = $(pwd)
mkdir Profilers/Examples/build
cd Profilers/Examples/build
cp "$GTPIN_DIR/OpcodeprofFiles/"* ../ -r
cmake .. -DCMAKE_BUILD_TYPE=Release -DARCH=intel64 -DGTPIN_KIT="$GTPIN_DIR/Profilers/"
make -j 8 install
```




