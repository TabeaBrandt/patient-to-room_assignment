def is_instance_feasible(filename):
    data = read_json(filename)
    if is_capacity_two(filename):
        return constant_capacity_instance_is_feasible(
            data["patients"], len(data["rooms"]), data["rooms"][0]["capacity"]
        )
    else:
        return is_instance_with_double_and_single_rooms_feasible(
            data["patients"], data["rooms"]
        )


def are_all_wards_feasible(wardNames):
    for filename in wardNames:
        if is_instance_feasible(filename):
            print(filename, "feasible")
        else:
            print(filename, "infeasible")


def constant_capacity_instance_is_feasible_for_day_(
    nFemalePatients, nMalePatients, nRooms, capacity
):
    from math import floor

    return floor(nFemalePatients / capacity) + floor(nMalePatients / capacity) <= nRooms


def constant_capacity_instance_is_feasible(
    patients, nRooms, capacity, firstDay=0, lastDay=364
):
    from filter import (
        filterPatients,
        isFemale,
        isMale,
        isHospitalizedOnDay,
    )

    return all(
        [
            constant_capacity_instance_is_feasible_for_day_(
                len(list(filterPatients([isFemale, isHospitalizedOnDay(d)], patients))),
                len(list(filterPatients([isMale, isHospitalizedOnDay(d)], patients))),
                nRooms,
                capacity,
            )
            for d in range(firstDay, lastDay + 1)
        ]
    )


def is_instance_with_double_and_single_rooms_feasible(
    patients, rooms, firstDay=0, lastDay=364
):
    from filter import (
        filterPatients,
        isHospitalizedOnDay,
    )

    totalCapacity = sum([r["capacity"] for r in rooms])
    return all(
        [
            len(list(filterPatients([isHospitalizedOnDay(d)], patients)))
            <= totalCapacity
            for d in range(firstDay, lastDay + 1)
        ]
    )


def compute_max_single_rooms_for_private_patients(patients, nRooms):
    from filter import (
        filterPatients,
        getPatientIDs,
        isFemale,
        isMale,
        isPrivate,
        isHospitalizedOnDay,
        isRegisteredOnDay,
        isNotPrivate,
    )
    from math import ceil

    alpha = (
        nRooms
        - ceil(
            0.5
            * len(
                list(filterPatients([isFemale, isNotPrivate], patients, onlyIDs=True))
            )
        )
        - ceil(
            0.5
            * len(list(filterPatients([isMale, isNotPrivate], patients, onlyIDs=True)))
        )
    )
    betaF = min(
        len(list(filterPatients([isFemale, isNotPrivate], patients, onlyIDs=True))) % 2,
        len(list(filterPatients([isFemale, isPrivate], patients, onlyIDs=True))),
    )
    betaM = min(
        len(list(filterPatients([isMale, isNotPrivate], patients, onlyIDs=True))) % 2,
        len(list(filterPatients([isMale, isPrivate], patients, onlyIDs=True))),
    )
    nPriv = len(list(filterPatients([isPrivate], patients, onlyIDs=True)))
    if nPriv <= alpha:
        return nPriv
    elif alpha == nPriv - 1 and betaF == 1 and betaM == 1:
        return nPriv - 1
    return 2 * alpha + betaF + betaM - nPriv


def get_total_smax(patients, nRooms, lastDay, firstDay=0):
    from filter import filterPatients, isPrivate, isHospitalizedOnDay

    return sum(
        [
            compute_max_single_rooms_for_private_patients(
                filterPatients([isHospitalizedOnDay(day)], patients), nRooms
            )
            for day in range(firstDay, lastDay + 1)
        ]
    )


def get_total_days_of_private_patients(lastDay, patients, firstDay=0):
    from filter import filterPatients, isPrivate, isHospitalizedOnDay

    return sum(
        [
            len(list(filterPatients([isHospitalizedOnDay(day), isPrivate], patients)))
            for day in range(firstDay, lastDay + 1)
        ]
    )


def is_capacity_in_one_two(filename):
    data = read_json(filename)
    for r in data["rooms"]:
        if r["capacity"] > 2:
            return False
    return True


def is_capacity_of_all_wards_in_one_two(wardNames):
    res = True
    for filename in wardNames:
        res = is_capacity_in_one_two(filename)
        if not res:
            print(filename, "capacity inconsistent")
            break
    print(res)


def is_capacity_two(filename):
    res = True
    data = read_json(filename)
    for r in data["rooms"]:
        if r["capacity"] != 2:
            return False
    return True


def get_smax_for_all_instances(allFiles):
    for filename in allFiles:
        startTime = time()
        data = read_json(filename)
        smax = get_total_smax(data["patients"], len(data["rooms"]), 364)
        endTime = time()
        print(filename, smax, round(endTime - startTime, 2))


def read_json(filename):
    import json

    with open(filename + ".json") as f:
        return json.load(f)


if __name__ == "__main__":
    from time import time
    from filter import (
        filterPatients,
        isHospitalizedOnDay,
    )

    folder = "instances"
    wardNames = ["0"]
    allFiles = [folder + "/" + w for w in wardNames]
    is_capacity_of_all_wards_in_one_two(allFiles)
    are_all_wards_feasible(allFiles)
    get_smax_for_all_instances(allFiles)
