# Configuration
CXX = g++
CXXFLAGS = -std=c++11 -Wall -Wextra -O2
SOURCE = race_condition.cpp
TARGET = race_condition

# OpenCL configuration
OPENCL_INCLUDE = -I/usr/include
OPENCL_LIBS = -lOpenCL

# Additional include/library paths (uncomment if needed)
# OPENCL_INCLUDE += -I/opt/intel/opencl/include
# OPENCL_LIBS += -L/opt/intel/opencl/lib64

all: $(TARGET)

$(TARGET): $(SOURCE)
	$(CXX) $(CXXFLAGS) $(OPENCL_INCLUDE) -o $(TARGET) $(SOURCE) $(OPENCL_LIBS)

clean:
	rm -f $(TARGET)

.PHONY: all clean
