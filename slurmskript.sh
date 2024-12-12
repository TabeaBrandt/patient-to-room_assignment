#!/bin/bash
 
# Array containing all instance names
 
declare -a instances=($(seq 0 80 $end))
# For all instances
for instance in ${instances[@]}
do
    # For all potential configs
    declare -a indices=($(seq 18 18 $end))
    for index in ${indices[@]}
    do
        # Submit the job to SLURM
        sbatch jobscript.sh "sra-1/load_80" $instance $index
    done
done
