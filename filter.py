def isPrivate(p):
    return p["isPrivate"]


def isNotPrivate(p):
    return not isPrivate(p)


def isFemale(p):
    return p["sex"] == "W"


def isMale(p):
    return p["sex"] == "M"


def is50Plus(p):
    return p["age"] >= 50


def __isHospitalizedOnDay(p, d):
    return (p["admission"] <= d) and (d < p["discharge"])


def isHospitalizedOnDay(d):
    return lambda p: __isHospitalizedOnDay(p, d)


def __isRegisteredOnDay(p, d):
    return (p["registration"] <= d) and (d < p["discharge"])


def isRegisteredOnDay(d):
    return lambda p: __isRegisteredOnDay(p, d)


def __isHospitalizedInInterval(p, firstDay, lastDay):
    return max(p["admission"], firstDay) <= min(p["discharge"] - 1, lastDay)


def isHospitalizedInInterval(firstDay, lastDay):
    return lambda p: __isHospitalizedInInterval(p, firstDay, lastDay)


def getPatientIDs(patients):
    return list(map(lambda p: p["id"], patients))


def filterPatients(filters, patients, onlyIDs=False):
    if onlyIDs:
        return getPatientIDs(filterPatients(filters, patients))
    return list(filter(lambda p: all([f(p) for f in filters]), patients))


def get_patient_IDs_with_relevant_days(patients, firstDay, lastDay):
    return [
        {
            "patientID": p["id"],
            "first_relevant_day": max(p["admission"], firstDay),
            "last_relevant_day": min(p["discharge"] - 1, lastDay),
        }
        for p in filterPatients([isHospitalizedInInterval(firstDay, lastDay)], patients)
    ]
