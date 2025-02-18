def init_result():
    return {
        "model_name": {},
        "objective_setup": {},
        "patient_assignments": {},
        "transfers": {},
        "private_rooms": {},
        "optimization_time": {},
        "mipGap": {},
        "runtime": {},
        "options": {},
        "roommatescore": {},
        "status": {},
    }


def get_current_patient_assignment(result, patients, newDay):
    from filter import filterPatients, isHospitalizedOnDay

    relevantPatientIDs = filterPatients(
        [isHospitalizedOnDay(newDay - 1), isHospitalizedOnDay(newDay)],
        patients,
        onlyIDs=True,
    )
    return {
        pID: result["patient_assignments"][pID][-1]["roomName"]
        for pID in relevantPatientIDs
    }


def append_result(result, new_result, firstDay=0):
    def merge_patient_assignments(patient_assignments, new_patient_assignments):
        for pID in new_patient_assignments.keys():
            if pID in patient_assignments.keys():
                last_old_entry = patient_assignments[pID][-1]
                first_new_entry = new_patient_assignments[pID][0]
                if last_old_entry["start"] == first_new_entry["start"]:
                    patient_assignments[pID] = (
                        patient_assignments[pID][:-1] + new_patient_assignments[pID]
                    )
                elif last_old_entry["roomName"] != first_new_entry["roomName"]:
                    assert (
                        last_old_entry["start"] < first_new_entry["start"]
                    ), "something went wrong up with the new IP results"
                    combined_entry = {
                        "start": last_old_entry["start"],
                        "end": first_new_entry["start"] - 1,
                        "roomName": last_old_entry["roomName"],
                    }
                    patient_assignments[pID] = (
                        patient_assignments[pID][:-1]
                        + [combined_entry]
                        + new_patient_assignments[pID]
                    )
            else:
                patient_assignments[pID] = new_patient_assignments[pID]
        return patient_assignments

    def merge_information_per_day(information_per_day, new_information_per_day):
        return {**information_per_day, **new_information_per_day}

    def append_information_firstDay(information_per_day, new_information_per_day, firstDay=firstDay):
        for key in new_information_per_day.keys():
            if key in information_per_day:
                information_per_day[key] += new_information_per_day[key]
            else:
                information_per_day[key] = new_information_per_day[key]
        return information_per_day

    if new_result["status"] == 3 or new_result["status"] == 9:
        return {
            "model_name": append_information_firstDay(
                result["model_name"], new_result["model_name"]
            ),
            "status": append_information_firstDay(
                result["status"], new_result["status"]
            ),
            "objective_setup": append_information_firstDay(
                result["objective_setup"], new_result["objective_setup"]
            ),
            "optimization_time": append_information_firstDay(
                result["optimization_time"], new_result["optimization_time"]
            ),
        }

    return {
        "model_name": append_information_firstDay(
            result["model_name"], new_result["model_name"]
        ),
        "status": append_information_firstDay(
            result["status"], new_result["status"]
        ),
        "objective_setup": append_information_firstDay(
            result["objective_setup"], new_result["objective_setup"]
        ),
        "patient_assignments": merge_patient_assignments(
            result["patient_assignments"], new_result["patient_assignments"]
        ),
        "transfers": merge_information_per_day(
            result["transfers"], new_result["transfers"]
        ),
        "private_rooms": merge_information_per_day(
            result["private_rooms"], new_result["private_rooms"]
        ),
        "runtime": merge_information_per_day(result["runtime"], new_result["runtime"]),
        "optimization_time": append_information_firstDay(
            result["optimization_time"], new_result["optimization_time"]
        ),
        "mipGap": merge_information_per_day(result["mipGap"], new_result["mipGap"]),
        "roommatescore": merge_information_per_day(result["roommatescore"], new_result["roommatescore"]),
    }


def assign_patients(
    patients, day, lastDay, rooms, currentPatientAssignment, timeLimit=60,roommates=True, get_pref=None,
):
    from Ipr import (
        IP,
        allow_transfers_of_hospitalized_patients,
        single_room_capacity_sex_separation_constraint_pr,
        fix_wmin,
        optimize_preferences,
        bounded_age_difference_pref,
    )
    from Iprt import IP_prt, fix_smax, single_room_capacity_sex_separation_constraint, optimize_preferences_prt, optimize_smax

    newResult = {}

    # Only run the first two models if all room have two beds or less.
    # This is done as the amount of private patients that can be assigned to a single room cannot
    # be computed if there is a room with more than two beds. This check can be removed once a new way
    # of computing this target has been implemented.
    if all(room["capacity"] <= 2 for room in rooms):
        newResult = IP(
            patients,
            day,
            lastDay,
            rooms,
    #        modelname="V",
            modelname="U",
            currentPatientAssignment=currentPatientAssignment,
            constraints=[single_room_capacity_sex_separation_constraint_pr, fix_smax],
            fPrio={"ftrans": 0, "fpriv": 0, "fpref": -1},
            fWeight={"ftrans": 0, "fpriv": 0, "fpref": -1},
            timeLimit=10,
            roommates = roommates,
            get_pref=get_pref,
    #        preference_setup=[fix_wmin],
            preference_setup=[optimize_preferences],
        )
        if "patient_assignments" not in newResult.keys():
            newResult = IP(
                patients,
                day,
                lastDay,
                rooms,
                currentPatientAssignment=currentPatientAssignment,
                modelname="U*",
                fPrio={"ftrans": 0, "fpriv": 0, "fpref": -1},
                fWeight={"ftrans": 1, "fpriv": 0, "fpref": -1},
                constraints=[single_room_capacity_sex_separation_constraint_pr, fix_smax],
                current_assignment_condition=allow_transfers_of_hospitalized_patients,
                timeLimit=10,
                roommates = roommates,
                get_pref=get_pref,
                preference_setup=[optimize_preferences],
            )
    else:
        # optimization of compatible roommates is currently only implemented for room capacities <= 2
        roommates = False
    # Continue with the last two models if there is a room with more than two beds or the previous
    # two models coudn't produce a result.
    if "patient_assignments" not in newResult.keys():
        newResult = IP(
            patients,
            day,
            lastDay,
            rooms,
            currentPatientAssignment=currentPatientAssignment,
            modelname="T*",
            fPrio={"ftrans": 1, "fpriv": 0, "fpref": -1},
            fWeight={"ftrans": 1, "fpriv": 1, "fpref": -1},
            constraints=[single_room_capacity_sex_separation_constraint_pr],
            current_assignment_condition=allow_transfers_of_hospitalized_patients,
            timeLimit=20,
            roommates = roommates,
            get_pref=get_pref,
            preference_setup=[optimize_preferences,optimize_smax],
        )
    if "patient_assignments" not in newResult.keys():
        newResult = IP_prt(
            patients,
            day,
            lastDay,
            rooms,
            modelname="Q",
            currentPatientAssignment=currentPatientAssignment,
            constraints=[single_room_capacity_sex_separation_constraint,break_symmetry],
            fPrio={"ftrans": 1, "fpriv": 0, "fpref": -1},
            fWeight={"ftrans": -1, "fpriv": 1, "fpref": -1},
            timeLimit=timeLimit,
            roommates = roommates,
            get_pref=get_pref,
            preference_setup=[optimize_preferences_prt,optimize_smax],
        )
    return newResult


def dynamic(
    file,
    fileNameOut,
    timeLimit=60,
    lastDay=364,
    roommates = True,
    get_pref= None,
):
    import json
    import codecs
    from filter import (
        filterPatients,
        getPatientIDs,
        isFemale,
        isMale,
        isPrivate,
        isHospitalizedOnDay,
        isRegisteredOnDay,
        isHospitalizedInInterval,
    )
    from time import time
    from os.path import join

    from Ipr import bounded_age_difference_pref

    print(file, fileNameOut)
    startTime = time()

    with open(file + ".json") as f:
        d = json.load(f)
        rooms = d["rooms"]
    result = init_result()
    for day in range(lastDay + 1):
        startTimeDay = time()
        print(day)
        patients = filterPatients([isRegisteredOnDay(day)], d["patients"])
        currentPatientAssignment = get_current_patient_assignment(result, patients, day)
        newResult = assign_patients(
            patients, day, lastDay, rooms, currentPatientAssignment, timeLimit=timeLimit,roommates=roommates, get_pref=get_pref
        )
        assert newResult, "ERROR, I_prt is infeasible"
        endTimeDay = time()
        newResult["runtime"] = {day: endTimeDay - startTimeDay}
        result = append_result(result, newResult)
    endTime = time()
    result["total_runtime"] = endTime - startTime
    from os.path import join
    with codecs.open(
        join("Results",file+"_"+fileNameOut+".json"), "w", encoding="utf-8"
    ) as out:
        out.write(json.dumps(result, indent=4))
    return result


if __name__ == "__main__":
    from Ipr import weighted_age_pref, age_classes_pref, absolut_age_difference_pref, bounded_age_difference_pref
    dynamic("instances/load_50/1", "results",roommates=True,get_pref=bounded_age_difference_pref)
