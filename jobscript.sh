#!/usr/bin/bash
#
#SBATCH --job-name=PRA
#SBATCH --output=SlurmLog/PRA_Output-%j.txt
#
#SBATCH --cpus-per-task=16
#SBATCH --time=4:10:00
#SBATCH --mail-type=ALL
#SBATCH --mail-user=brandt@combi.rwth-aachen.de

module --ignore_cache load "Python/3.10.4"
module --ignore_cache load "GCC/13.2.0"
module --ignore_cache load "Gurobi/11.0.0"
module --ignore_cache load "networkx/3.2.1"
 
path="$1" # e.g. '2019'
instance="$2" # e.g. 'GC01'
index="$3" # integer

# Create output directory if it does not exist. 
mkdir -p "Results/"
mkdir -p "Results/"${path}
mkdir -p "Results/logs"
mkdir -p "Results/logs/"${path}
 
#Run code
python3 parseconfig.py ${path} ${instance} ${index}
