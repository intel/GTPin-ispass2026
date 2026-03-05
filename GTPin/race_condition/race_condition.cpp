/*========================== begin_copyright_notice ============================
Copyright (C) 2025 Intel Corporation

This software and the related documents are Intel copyrighted materials, and your
use of them is governed by the express license under which they were provided to
you ("License"). Unless the License provides otherwise, you may not use, modify,
copy, publish, distribute, disclose or transmit this software or the related
documents without Intel's prior written permission.

This software and the related documents are provided as is, with no express or
implied warranties, other than those that are expressly stated in the License.
============================= end_copyright_notice ===========================*/
#include <CL/cl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fstream>
#include <string>


char* FileToBuffer(const char* sFileName)
{
    // try to open file
    std::ifstream file(sFileName);
    if (file.fail())
    {
        // could not open file, return NULL
        return NULL;
    }
    file.seekg(0, std::ios::end);
    size_t length = file.tellg();
    file.seekg(0, std::ios::beg);
    char* buffer = new char[length + 1];
    file.read(buffer, length);
    buffer[file.gcount()] = '\0';
    // close file
    file.close();
    // return buffer
    return buffer;
}


int main(int argc, char** argv)
{
    int num_elements = 1024;
    int group = 64;
    bool print = false;
    bool race_condition = true;

    int arg = 1;
    for (;arg < argc;arg++)
    {
        if (std::string(argv[arg]) == "--num_elements" && arg < argc + 1)
        {
            num_elements = atoi(argv[arg+1]);
            arg++;
        }
        else if (std::string(argv[arg]) == "--group" && arg < argc + 1)
        {
            group = atoi(argv[arg+1]);
            arg++;
        }
        else if (std::string(argv[arg]) == "--print")
        {
             print = true;
        }
        else if (std::string(argv[arg]) == "--no_race")
        {
             race_condition = false;
        }
    }

    // Parse the number of elements from command-line arguments
    size_t data_size = num_elements * sizeof(int);

    // Allocate memory for the data array
    int* data = (int*)malloc(data_size);
    for (int i = 0; i < num_elements; i++)
    {
        data[i] = 0;
    }

    // Get platform and device information
    cl_platform_id platform_id = NULL;
    cl_device_id device_id = NULL;
    cl_uint ret_num_devices;
    cl_uint ret_num_platforms;
    cl_int ret = clGetPlatformIDs(1, &platform_id, &ret_num_platforms);
    ret = clGetDeviceIDs(platform_id, CL_DEVICE_TYPE_DEFAULT, 1, &device_id, &ret_num_devices);

    // Create an OpenCL context
    cl_context context = clCreateContext(NULL, 1, &device_id, NULL, NULL, &ret);

    // Create a command queue
    cl_command_queue command_queue = clCreateCommandQueue(context, device_id, 0, &ret);

    char* programSource = FileToBuffer("kernel.cl");
    if (NULL == programSource)
    {
        printf("Can't read kernels.cl!\n");
        clReleaseCommandQueue(command_queue);
        clReleaseContext(context);
        exit(-1);
    }
    printf("kernels.cl was read\n");

    // Create a memory buffer on the device for the data array
    cl_mem data_mem_obj = clCreateBuffer(context, CL_MEM_READ_WRITE, data_size, NULL, &ret);

    // Copy the data array to the memory buffer
    ret = clEnqueueWriteBuffer(command_queue, data_mem_obj, CL_TRUE, 0, data_size, data, 0, NULL, NULL);

    size_t srclen[] = { strlen(programSource) };
    cl_program program = clCreateProgramWithSource(context, 1, (const char**)&programSource, srclen, &ret);
    if (ret)
    {
        delete programSource;
        exit(-1);
    }
    if (program == (cl_program)0)
    {
        delete programSource;
        printf("Error in clCreateProgramWithSource.\n");
        exit(-1);
    }

    // Build the program
    ret = clBuildProgram(program, 1, &device_id, NULL, NULL, NULL);

    if (ret)
    {
        size_t log_size;
        clGetProgramBuildInfo(program, device_id, CL_PROGRAM_BUILD_LOG, 0, NULL, &log_size);
        char *log = (char *)malloc(log_size);
        clGetProgramBuildInfo(program, device_id, CL_PROGRAM_BUILD_LOG, log_size, log, NULL);
        printf("Build Log:\n%s\n", log);
        free(log);
    }

    // Create the OpenCL kernel
    const char* kernel_name = race_condition ? "race_condition_example" : "no_race_condition_example";
    cl_kernel kernel = clCreateKernel(program, kernel_name, &ret);

    // Set the arguments of the kernel
    ret = clSetKernelArg(kernel, 0, sizeof(cl_mem), (void*)&data_mem_obj);
    ret = clSetKernelArg(kernel, 1, sizeof(int), (void*)&num_elements);

    // Execute the OpenCL kernel on the array
    size_t global_item_size = num_elements; // Process the entire array
    size_t local_item_size = group; // Divide work-items into groups of 64
    ret = clEnqueueNDRangeKernel(command_queue, kernel, 1, NULL, &global_item_size, &local_item_size, 0, NULL, NULL);

    // Read the memory buffer back to the data array
    ret = clEnqueueReadBuffer(command_queue, data_mem_obj, CL_TRUE, 0, data_size, data, 0, NULL, NULL);

    if (print)
    {
        // Display the result
        for (int i = 0; i < num_elements; i++)
        {
            printf("data[%d] = %d\n", i, data[i]);
        }
    }

    // Clean up
    ret = clFlush(command_queue);
    ret = clFinish(command_queue);
    ret = clReleaseKernel(kernel);
    ret = clReleaseProgram(program);
    ret = clReleaseMemObject(data_mem_obj);
    ret = clReleaseCommandQueue(command_queue);
    ret = clReleaseContext(context);
    free(data);

    delete programSource;

    return EXIT_SUCCESS;
}