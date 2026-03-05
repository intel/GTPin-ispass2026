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
__kernel void race_condition_example(__global int* data, int num_elements)
{
    int gid = get_global_id(0);
    int lid = get_local_id(0);
    //printf("gid = %d lid = %d num_elements = %d\n", gid, lid, num_elements);
    if (gid < num_elements)
    {
        data[lid % num_elements] += 1;
    }
}

__kernel void no_race_condition_example(__global int* data, int num_elements)
{
    int gid = get_global_id(0);
    int lid = get_local_id(0);
    //printf("gid = %d lid = %d num_elements = %d\n", gid, lid, num_elements);
    if (gid < num_elements)
    {
        atomic_inc(&data[lid % num_elements]);
    }
}