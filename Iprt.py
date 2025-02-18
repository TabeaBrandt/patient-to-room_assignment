from Ipr import var_prt, var_rt, get_private_beds, weighted_age_pref, are_potential_roommates, pre_post_surgery_pref
def fix_wmin_prt(
    m, modelVars, patients, firstDay, lastDay,roommateTuples, get_pref, fPrio, fWeight, nRooms
):
    import gurobipy as gp
    from filter import (
        filterPatients,
        isFemale,
        isMale,
        isPrivate,
        isHospitalizedOnDay,
    )
    from analyze_instance import compute_wmin_score
    from Ipr import are_potential_roommates

    for t in range(firstDay, lastDay+1):
        hospitalizedPatients = filterPatients([isHospitalizedOnDay(t)], patients)
        np = len(hospitalizedPatients)
        roommateTuples = [ (hospitalizedPatients[i], hospitalizedPatients[j]) for i in range(np) for j in range(i+1,np) if are_potential_roommates(hospitalizedPatients[i],hospitalizedPatients[j]) ]
        preferenceSum = gp.quicksum(get_pref(p,q)*modelVars["y"][p["id"],q["id"],t] for (p,q) in roommateTuples)
        res = compute_wmin_score(hospitalizedPatients, nRooms, get_pref)
        m.addConstr(
            preferenceSum
            <= res
        )

def optimize_preferences_prt(
    m, modelVars, patients, firstDay, lastDay, roommateTuples,get_pref, fPrio, fWeight, nRooms
):
    import gurobipy as gp
    from filter import (
        filterPatients,
        isFemale,
        isMale,
        isPrivate,
        isHospitalizedOnDay,
    )

    preferenceObj = 0
    for day in range(firstDay, lastDay + 1):
        hospitalizedPatients = filterPatients([isHospitalizedOnDay(day)], patients)
        np = len(hospitalizedPatients)
        roommateTuples = [ (hospitalizedPatients[i], hospitalizedPatients[j]) for i in range(np) for j in range(i+1,np) if are_potential_roommates(hospitalizedPatients[i],hospitalizedPatients[j]) ]

        preferenceObj += gp.quicksum(get_pref(p,q)*modelVars["y"][p["id"],q["id"],day] for (p,q) in roommateTuples)
    m.setObjectiveN( # Link y to objective
        preferenceObj,
        1,
        priority=fPrio["fpref"],
        weight=fWeight["fpref"],
        name="preferencs",
    )

def optimize_smax(
    m, modelVars, patients, firstDay, lastDay, roommateTuples,get_pref, fPrio, fWeight, nRooms
):
    m.setObjectiveN(
        modelVars["s"].sum("*", "*", "*"),
        2,
        priority=fPrio["fpriv"],
        weight=fWeight["fpriv"],
        name="privates",
    )

def fix_smax(model, modelVars, patients, rooms, firstDay, lastDay,currentPatientAssignment):
    import gurobipy as gp
    from filter import (
        filterPatients,
        isPrivate,
        isHospitalizedOnDay,
    )
    from analyze_instance import compute_max_single_rooms_for_private_patients

    assert all(
        [r["capacity"] <= 2 for r in rooms]
    ), "upper bound on single rooms for private patients is only valid for rooms with at most two beds"

    for day in range(firstDay, lastDay + 1):
        hospitalizedPatients = filterPatients([isHospitalizedOnDay(day)], patients)
        smax = compute_max_single_rooms_for_private_patients(
            hospitalizedPatients, len(rooms)
        )
        model.addConstr(modelVars["s"].sum("*", "*", day) >= smax)


def single_room_capacity_sex_separation_constraint(
    model, modelVars, patients, rooms, firstDay, lastDay,currentPatientAssignment
):
    import gurobipy as gp
    from filter import (
        filterPatients,
        isFemale,
        isMale,
        isPrivate,
        isHospitalizedOnDay,
    )

    for day in range(firstDay, lastDay + 1):
        hospitalizedPatients = filterPatients([isHospitalizedOnDay(day)], patients)
        for r in rooms:
            sumFemalePatients = gp.quicksum(
                modelVars["x"][pID, r["name"], day]
                for pID in filterPatients(
                    [isFemale], hospitalizedPatients, onlyIDs=True
                )
            )
            sumMalePatients = gp.quicksum(
                modelVars["x"][pID, r["name"], day]
                for pID in filterPatients([isMale], hospitalizedPatients, onlyIDs=True)
            )
            sumFemalePrivatePatients = gp.quicksum(
                (r["capacity"] - 1) * modelVars["s"][pID, r["name"], day]
                for pID in filterPatients(
                    [isFemale, isPrivate], hospitalizedPatients, onlyIDs=True
                )
            )
            sumMalePrivatePatients = gp.quicksum(
                (r["capacity"] - 1) * modelVars["s"][pID, r["name"], day]
                for pID in filterPatients(
                    [isMale, isPrivate], hospitalizedPatients, onlyIDs=True
                )
            )
            model.addConstr(
                sumFemalePatients + sumFemalePrivatePatients
                <= r["capacity"] * modelVars["g"][r["name"], day]
            )
            model.addConstr(
                sumMalePatients + sumMalePrivatePatients
                <= r["capacity"] * (1 - modelVars["g"][r["name"], day])
            )


def IP_prt(
    patients,
    firstDay,
    lastDay,
    rooms,
    currentPatientAssignment={},
    modelname="H",
    timeLimit=60,
    fPrio={"ftrans": 0, "fpriv": 1},
    fWeight={"ftrans": -1, "fpriv": 1},
    optimizeTransfersOnly=False,
    constraints=[single_room_capacity_sex_separation_constraint,fix_smax],
    roommates=True,
    preference_setup=[optimize_preferences_prt],
    get_pref=weighted_age_pref,
):
    import gurobipy as gp
    from gurobipy import GRB

    from filter import (
        filterPatients,
        getPatientIDs,
        isFemale,
        isMale,
        isPrivate,
        isHospitalizedOnDay,
        get_patient_IDs_with_relevant_days,
    )
    from Ipr import var_prt, var_rt, get_private_beds, weighted_age_pref, are_potential_roommates, pre_post_surgery_pref

    def get_room(modelVars, patientID, day, roomNames):
        return list(
            filter(lambda r: modelVars["x"][p["patientID"], r, day].x > 0.5, roomNames)
        )[0]

    m = gp.Model(modelname)
    m.setParam("TimeLimit", timeLimit)

    roomNames = [r["name"] for r in rooms]
    x = var_prt(m, patients, roomNames, firstDay, lastDay, "Patient-Room Assignment")
    g = var_rt(m, roomNames, firstDay, lastDay, "is female in room")
    delta = var_prt(m, patients, roomNames, firstDay, lastDay, "transfers")
    modelVars = {"x": x, "g": g, "delta": delta}
    s = var_prt(
        m,
        filterPatients([isPrivate], patients),
        roomNames,
        firstDay,
        lastDay,
        "gets private patient a single room",
    )
    modelVars["s"] = s

    preAssignedPatientIDs = [
        pID
        for pID in list(getPatientIDs(patients))
        if pID in currentPatientAssignment.keys()
    ]
    transfersOfCurrentPatients = len(preAssignedPatientIDs) - gp.quicksum(
        modelVars["x"][pID, currentPatientAssignment[pID],firstDay]
        for pID in preAssignedPatientIDs
    )

    preferenceObj = 0
    roommateIDtuples = []
    for day in range(firstDay, lastDay + 1):
        hospitalizedPatients = filterPatients([isHospitalizedOnDay(day)], patients)
        m.addConstrs(
            x.sum(pID, "*", day) == 1 for pID in getPatientIDs(hospitalizedPatients)
        )
        if roommates:
            np = len(hospitalizedPatients)
            roommateTuples = [ (hospitalizedPatients[i], hospitalizedPatients[j]) for i in range(np) for j in range(i+1,np) if are_potential_roommates(hospitalizedPatients[i],hospitalizedPatients[j]) ]
            roommateIDtuples += [(p["id"],q["id"],day) for (p,q) in roommateTuples]
        for r in rooms:
            if not optimizeTransfersOnly:
                m.addConstrs(
                    s[pID, r["name"], day] <= x[pID, r["name"], day]
                    for pID in filterPatients(
                        [isPrivate], hospitalizedPatients, onlyIDs=True
                    )
                )
    if roommates:
        modelVars["y"] = m.addVars(roommateIDtuples, vtype=GRB.BINARY, name='roommates')
        m.addConstrs(modelVars["y"][pID,qID,day] >= modelVars["x"][pID,rName,day] + modelVars["x"][qID,rName,day] -1 for (pID,qID,day) in roommateIDtuples for rName in roomNames)
        for c in preference_setup:
            c(m, modelVars, patients, firstDay, lastDay, roommateIDtuples, get_pref,fPrio, fWeight, len(rooms))
    for day in range(firstDay, lastDay):
        hospitalizedPatients = filterPatients([isHospitalizedOnDay(day)], patients)
        for r in rooms:
            m.addConstrs(
                x[pID, r["name"], day] - x[pID, r["name"], day + 1]
                <= delta[pID, r["name"], day]
                for pID in filterPatients(
                    [isHospitalizedOnDay(day + 1)], hospitalizedPatients, onlyIDs=True
                )
            )
    for c in constraints:
        c(m, modelVars, patients, rooms, firstDay, lastDay,currentPatientAssignment)
    transfers = delta.sum("*", "*", "*") + transfersOfCurrentPatients
    if optimizeTransfersOnly:
        m.setObjective(transfers)
        m.ModelSense = GRB.MINIMIZE
    else:
        m.ModelSense = GRB.MAXIMIZE
        m.setObjectiveN(
            transfers,
            0,
            priority=fPrio["ftrans"],
            weight=fWeight["ftrans"],
            name="transfers",
        )

    m.setParam(GRB.Param.PoolSolutions, 100)

    m.optimize()
    print("Model status:")
    print(m.Status)
    nObjectives = m.NumObj
    objPrios = {}
    if nObjectives > 1:
        for o in range(nObjectives):
            m.params.ObjNumber = o
            objPrios[m.ObjNName] = m.ObjNPriority
    if m.Status == GRB.INFEASIBLE or m.Status == GRB.INF_OR_UNBD or (m.Status == GRB.TIME_LIMIT and m.SolCount == 0):
        return {
            "model_name": {firstDay: [m.ModelName]},
            "status": {firstDay: [m.Status]},
            "objective_setup": {firstDay: [objPrios]},
            "optimization_time": {firstDay: [round(m.Runtime, 5)]},
        }
    if m.Status != GRB.OPTIMAL:
        mipGap = 100
    else:
        mipGap = 0.0

    patient_assignments = {}
    for p in get_patient_IDs_with_relevant_days(patients, firstDay, lastDay):
        patient_assignments[p["patientID"]] = [
            {
                "start": p["first_relevant_day"],
                "end": p["first_relevant_day"],
                "roomName": get_room(
                    modelVars, p["patientID"], p["first_relevant_day"], roomNames
                ),
            }
        ]
        for day in range(p["first_relevant_day"] + 1, p["last_relevant_day"] + 1):
            assert (
                patient_assignments[p["patientID"]][-1]["end"] == day - 1
            ), "there is a gap in the patient assignments"
            newRoomName = get_room(modelVars, p["patientID"], day, roomNames)
            if newRoomName == patient_assignments[p["patientID"]][-1]["roomName"]:
                patient_assignments[p["patientID"]][-1]["end"] = day
            else:
                patient_assignments[p["patientID"]].append(
                    {"start": day, "end": day, "roomName": newRoomName}
                )
    daylyTransfers = {
        d: round(modelVars["delta"].sum("*", "*", d).getValue())
        for d in range(firstDay, lastDay + 1)
    }
    nPrivatebeds = get_private_beds(modelVars, firstDay, lastDay)

    allScores = {}
    if roommates:
        for day in range(firstDay, lastDay+1):
            hospitalizedPatients = filterPatients([isHospitalizedOnDay(day)], patients)
            roommatescore = []
            for p in hospitalizedPatients:
                for q in hospitalizedPatients:
                    if p['id'] != q['id'] and are_potential_roommates(p,q):
                        if (q['id'],p['id'],day) in modelVars["y"].keys(): continue
                        if modelVars["y"][p['id'],q['id'],day].x > 0.99:
                            roommatescore.append(get_pref(p,q))
            allScores[day] = sum(roommatescore)

    return {
        "model_name": {firstDay: [m.ModelName]},
        "status": {firstDay: [m.Status]},
        "objective_setup": {firstDay: [objPrios]},
        "patient_assignments": patient_assignments,
        "transfers": daylyTransfers,
        "total_transfers": round(transfers.getValue()),
        "private_rooms": nPrivatebeds,
        "optimization_time": {firstDay: [round(m.Runtime, 5)]},
        "mipGap": {firstDay: mipGap},
        "roommatescore": allScores,
    }
