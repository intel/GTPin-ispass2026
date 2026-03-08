/*========================== begin_copyright_notice ============================
Copyright (C) 2026 Intel Corporation

SPDX-License-Identifier: MIT
============================= end_copyright_notice ===========================*/

__kernel void race_condition_example(__global int* data, int num_elements)
{
    int gid = get_global_id(0);
    int lid = get_local_id(0);

    if (gid < num_elements)
    {
        data[lid % num_elements] += 1;
    }
}

__kernel void no_race_condition_example(__global int* data, int num_elements)
{
    int gid = get_global_id(0);
    int lid = get_local_id(0);

    if (gid < num_elements)
    {
        atomic_inc(&data[lid % num_elements]);
    }
}