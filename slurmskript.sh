#!/bin/bash
 
# Array containing all instance names
declare -a instances=("0")
 
# For all instances
for instance in ${instances[@]}
do
    # For all potential configs
    declare -a indices=($(seq 0 18 $end))
    for index in ${indices[@]}
    do
        # Submit the job to SLURM
        sbatch jobscript.sh "instances" $instance $index
    done
done
