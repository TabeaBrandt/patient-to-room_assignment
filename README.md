# Patient-to-Room Assignment
This repository provides you with the code of our computational study as described in our paper **Structural insights and an LP-based solution method for patient-to-room assignment under consideration of single room entitlements**.

You're welcome to use and develop it further as long as you include a citation of our paper as reference. If you have any questions, feel free to contact us via brandt@combi.rwth-aachen.de or engelhardt@combi.rwth-aachen.de.

## Installation and Dependencies
No installation is required. You can download and execute the repository as it is. We assume you have a working *python* and *gurobipy* installation.

Note that we use [Gurobi](https://www.gurobi.com/) as a Integer Linear Programming solver. *Gurobi* is a commercial product, but free licenses are available for academics and students. You need both a working *Gurobi* installation and a valid license to execute the code. *Gurobi* interfaces with *python* via the *gurobipy* package. The latter can, again, be installed via, e.g. *pip* or *conda*.

## Excecuting Code
You can either use the code to solve a single patient-to-room assignment (PRA) problem, i.e. the static case or you can use it to solve a sequence of PRA problems via a rolling-time-horizon appproach including making use of multiple Integer Programming formulations, i.e. the dynamic case. Per default, one instance called '0' is given that can be used for testing. Make sure to execute the files in the given folder structure or to change filepaths accordingly.

### Dynamic case
For the dynamic case, execute "Dynamic.py". Two parameters need to be specified:

- file, the name/filepath of the instance to be read in
- fileNameOut, the name/filepath of the file to write the results to

There are three optional parameters where default values are given for testing:
- timeLimit, the maximum runtime per step in seconds
- lastDay, the final day until which the model determines an assignment, default starting day is 0
- fPrio, a dictionary assigning a priority value to "ftrans" and "fpriv", i.e. minimising transfers and maximising single room entitlements. Here, 0 is the most important priority and larger values mean lower priority

All other parameters are fixed according to the "assign_patients" function.

### Static case
For the static case, execute "Static.py". More parameters are allow testing a variety of IP formulations. Thus, on top of the parameters given for the dynamic case, you also can specify the following:

- firstDay, the first day from which onwards the model schedules patients
- ip_fkt, weather a IP formulation with x_prt assignment variables (IP_prt) or x_rt assignment variables (IP_rt) is to be used. note that the latter is vastly faster, but may lead to infeasible solutions, as most transfers are disallowed
- fWeight, a dictionary assigning weights to different objective parts "ftrans" and "fpriv". Per default, transfers are minimised and single room assignments for private patients are maximised
- constraints, list of constraints that are to be used. Each constraint type  (as explained below) can be added in modular fashion
- useVarMrt, specifies whether there are two disjoint variable set for male and female rooms (True) or one variable set of variables that are either 0 or 1 depending on the gender a room is assigned to (False)

Check out the file "config.py" for an overview of different parameter configurations.

### Constraint types
The following constraint types can be used:

- capacity_constraint, default constraints so rooms are not overbooked
- sex_separation_constraint, default constraints so male and female patients do not share a room 
- capacity_sex_separation_constraint, combination of the above
- single_room_constraint, constraint type that models single room assignments
- single_room_constraint_pr, variation of the above for x_pr type variables
- single_room_capacity_sex_separation_constraint, constraint type that models single room assignments in combination with sex seperation
- single_room_capacity_sex_separation_constraint_pr, variation of the above for x_pr type variables
- fix_smax, fixes the objective values of single room entitlements to its maximum value, which is determined combinatorically
- fix_smax_eq, variation of the above that enforces that the single room entitlement objective is bigger or equal to its maximum

## Using a computing cluster 
The following is only relevant, if you wish to run experiments on a computing cluster. Note that this also requires that all of the dependencies mentioned above, including *Gurobi*, are installed at the cluster in question.

We did our computational study on the [RWTH Aachen High Performance Computing Cluster](https://help.itc.rwth-aachen.de/service/rhr4fjjutttf/), which uses a Linux based job scheduling based on *slurm*. *Slurm* is an open source job management tool, the respective *slurm* files are are also given. 

Just execute the "jocscript.sh" to execute a single job. The parameters "path", "instance" and "index" need to be specified as in the given examples.

By executing the "slurmscript.sh" you can execute multiple jobs at once. 

## Other files
"Ipr.py" and "Iprt.py" containt the actual IP formulations. "analyze_instance.py" contains auxilliary functions, so does "filter.py". Finally, "config.py" contains different parameter configurations that were used in our computational study, which can be parsed via "parseconfig.py".
