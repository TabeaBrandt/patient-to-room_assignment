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


def append_result(result, new_result):
    def merge_patient_assignments(patient_assignments, new_patient_assignments):
        for pID in new_patient_assignments.keys():
            if pID in patient_assignments.keys():
                last_old_entry = patient_assignments[pID][-1]
                first_new_entry = new_patient_assignments[pID][0]
                if last_old_entry["start"] == first_new_entry["start"]:
                    patient_assignments[pID] = (
                        patient_assignments[pID][:-1] + [first_new_entry]
                    )
                elif last_old_entry["roomName"] != first_new_entry["roomName"]:
                    assert (
                        last_old_entry["start"] < first_new_entry["start"]
                    ), "something went wrong up with the new IP results" +'\n'+ str(patient_assignments[pID]) +'\n'+ str(new_patient_assignments[pID])
                    combined_entry = {
                        "start": last_old_entry["start"],
                        "end": first_new_entry["start"] - 1,
                        "roomName": last_old_entry["roomName"],
                    }
                    patient_assignments[pID] = (
                        patient_assignments[pID][:-1]
                        + [combined_entry]
                        + [first_new_entry]
                    )
            else:
                patient_assignments[pID] = [new_patient_assignments[pID][0]]
        return patient_assignments

    def merge_information_per_day(information_per_day, new_information_per_day):
        return {**information_per_day, **new_information_per_day}

    return {
        "model_name": merge_information_per_day(
            result["model_name"], new_result["model_name"]
        ),
        "objective_setup": merge_information_per_day(
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
        "optimization_time": merge_information_per_day(
            result["optimization_time"], new_result["optimization_time"]
        ),
        "mipGap": merge_information_per_day(result["mipGap"], new_result["mipGap"]),
    }


def assign_patients(
    patients, day, lastDay, rooms, currentPatientAssignment, timeLimit=60
):
    from Ipr import (
        IP,
        allow_transfers_of_hospitalized_patients,
        single_room_capacity_sex_separation_constraint_pr,
    )
    from Iprt import IP_prt, fix_smax, single_room_capacity_sex_separation_constraint

    newResult = IP(
        patients,
        day,
        lastDay,
        rooms,
        modelname="P",
        currentPatientAssignment=currentPatientAssignment,
        constraints=[single_room_capacity_sex_separation_constraint_pr, fix_smax],
        fPrio={"ftrans": 0, "fpriv": 0},
        fWeight={"ftrans": 0, "fpriv": 0},
        timeLimit=10,
    )
    if not newResult:
        newResult = IP(
            patients,
            day,
            lastDay,
            rooms,
            currentPatientAssignment=currentPatientAssignment,
            modelname="P*",
            fPrio={"ftrans": 0, "fpriv": 0},
            fWeight={"ftrans": 1, "fpriv": 0},
            constraints=[single_room_capacity_sex_separation_constraint_pr, fix_smax],
            current_assignment_condition=allow_transfers_of_hospitalized_patients,
            timeLimit=10,
        )
    if not newResult:
        newResult = IP(
            patients,
            day,
            lastDay,
            rooms,
            currentPatientAssignment=currentPatientAssignment,
            modelname="O",
            fPrio={"ftrans": 1, "fpriv": 0},
            fWeight={"ftrans": 1, "fpriv": 1},
            constraints=[single_room_capacity_sex_separation_constraint_pr],
            current_assignment_condition=allow_transfers_of_hospitalized_patients,
            timeLimit=20,
        )
    if not newResult:
        newResult = IP_prt(
            patients,
            day,
            lastDay,
            rooms,
            modelname="H",
            currentPatientAssignment=currentPatientAssignment,
            constraints=[single_room_capacity_sex_separation_constraint],
            fPrio={"ftrans": 1, "fpriv": 0},
            fWeight={"ftrans": -1, "fpriv": 1},
            timeLimit=timeLimit,
        )
    return newResult


def dynamic(
    file,
    fileNameOut,
    timeLimit=60,
    lastDay=364,
    fPrio={"ftrans": 0, "fpriv": 1},
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
            patients, day, lastDay, rooms, currentPatientAssignment, timeLimit=timeLimit
        )
        assert newResult, "ERROR, I_prt is infeasible"
        endTimeDay = time()
        newResult["runtime"] = {day: endTimeDay - startTimeDay}
        result = append_result(result, newResult)
    endTime = time()
    result["total_runtime"] = endTime - startTime
    with codecs.open(
        "Results/" + file + "_" + fileNameOut + ".json", "w", encoding="utf-8"
    ) as out:
        out.write(json.dumps(result, indent=4))


if __name__ == "__main__":
    dynamic("2019/UC01", "dyn_test_out")
