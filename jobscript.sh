#!/usr/bin/bash
#
#SBATCH --job-name=PRA
#SBATCH --output=SlurmLog/PRA_Output-%j.txt
#
#SBATCH --cpus-per-task=32
#SBATCH --time=12:10:00
#SBATCH --mem-per-cpu=3900
#SBATCH --mail-type=ALL
#SBATCH --mail-user=brandt@combi.rwth-aachen.de
#SBATCH --partition=c23mm

module --ignore_cache load "GCCcore/.12.3.0"
module --ignore_cache load "GCCcore/.13.2.0"
module --ignore_cache load "Gurobi/11.0.0"
 
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
