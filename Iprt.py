def fix_smax(model, modelVars, useVarMrt, patients, rooms, firstDay, lastDay):
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


def fix_smax_eq(model, modelVars, useVarMrt, patients, rooms, firstDay, lastDay):
    import gurobipy as gp
    from filter import (
        filterPatients,
        isPrivate,
        isHospitalizedOnDay,
    )
    from analyze_instance import compute_max_single_rooms_for_private_patients

    for day in range(firstDay, lastDay + 1):
        hospitalizedPatients = filterPatients([isHospitalizedOnDay(day)], patients)
        smax = compute_max_single_rooms_for_private_patients(
            hospitalizedPatients, len(rooms)
        )
        model.addConstr(modelVars["s"].sum("*", "*", day) == smax)


def capacity_constraint(
    model, modelVars, useVarMrt, patients, rooms, firstDay, lastDay
):
    import gurobipy as gp
    from filter import (
        filterPatients,
        isFemale,
        isMale,
        isHospitalizedOnDay,
    )

    for day in range(firstDay, lastDay + 1):
        hospitalizedPatients = filterPatients([isHospitalizedOnDay(day)], patients)
        for r in rooms:
            model.addConstr(modelVars["x"].sum("*", r["name"], day) <= r["capacity"])


def sex_separation_constraint(
    model, modelVars, useVarMrt, patients, rooms, firstDay, lastDay
):
    import gurobipy as gp
    from filter import (
        filterPatients,
        isFemale,
        isMale,
        isHospitalizedOnDay,
    )

    for day in range(firstDay, lastDay + 1):
        hospitalizedPatients = filterPatients([isHospitalizedOnDay(day)], patients)
        for r in rooms:
            for p in filterPatients([isFemale], hospitalizedPatients, onlyIDs=True):
                model.addConstr(
                    modelVars["x"][p, r["name"], day] <= modelVars["g"][r["name"], day]
                )
            for p in filterPatients([isMale], hospitalizedPatients, onlyIDs=True):
                if useVarMrt:
                    model.addConstr(
                        modelVars["x"][p, r["name"], day]
                        <= modelVars["m"][r["name"], day]
                    )
                else:
                    model.addConstr(
                        modelVars["x"][p, r["name"], day]
                        <= 1 - modelVars["g"][r["name"], day]
                    )


def capacity_sex_separation_constraint(
    model, modelVars, useVarMrt, patients, rooms, firstDay, lastDay
):
    import gurobipy as gp
    from filter import (
        filterPatients,
        isFemale,
        isMale,
        isHospitalizedOnDay,
    )

    for day in range(firstDay, lastDay + 1):
        hospitalizedPatients = filterPatients([isHospitalizedOnDay(day)], patients)
        for r in rooms:
            model.addConstr(
                gp.quicksum(
                    modelVars["x"][p, r["name"], day]
                    for p in filterPatients(
                        [isFemale], hospitalizedPatients, onlyIDs=True
                    )
                )
                <= r["capacity"] * modelVars["g"][r["name"], day]
            )
            if useVarMrt:
                model.addConstr(
                    gp.quicksum(
                        modelVars["x"][p, r["name"], day]
                        for p in filterPatients(
                            [isMale], hospitalizedPatients, onlyIDs=True
                        )
                    )
                    <= r["capacity"] * modelVars["m"][r["name"], day]
                )
            else:
                model.addConstr(
                    gp.quicksum(
                        modelVars["x"][p, r["name"], day]
                        for p in filterPatients(
                            [isMale], hospitalizedPatients, onlyIDs=True
                        )
                    )
                    <= r["capacity"] * (1 - modelVars["g"][r["name"], day])
                )


def single_room_constraint(
    model, modelVars, useVarMrt, patients, rooms, firstDay, lastDay
):
    import gurobipy as gp
    from filter import (
        filterPatients,
        isPrivate,
        isHospitalizedOnDay,
        getPatientIDs,
    )

    for day in range(firstDay, lastDay + 1):
        hospitalizedPatients = filterPatients([isHospitalizedOnDay(day)], patients)
        for r in rooms:
            for p in filterPatients([isPrivate], hospitalizedPatients, onlyIDs=True):
                model.addConstr(
                    r["capacity"] * modelVars["s"][p, r["name"], day]
                    + gp.quicksum(
                        modelVars["x"][q, r["name"], day]
                        for q in getPatientIDs(hospitalizedPatients)
                    )
                    <= r["capacity"] + modelVars["x"][p, r["name"], day]
                )


def single_room_capacity_sex_separation_constraint(
    model, modelVars, useVarMrt, patients, rooms, firstDay, lastDay
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
            if useVarMrt:
                model.addConstr(
                    sumMalePatients + sumMalePrivatePatients
                    <= r["capacity"] * modelVars["m"][r["name"], day]
                )
            else:
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
    useVarMrt=False,
    optimizeTransfersOnly=False,
    constraints=[single_room_capacity_sex_separation_constraint],
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
    from Ipr import var_prt, var_rt, get_private_beds

    def get_room(modelVars, patientID, day, roomNames):
        return list(
            filter(lambda r: modelVars["x"][patientID, r, day].x > 0.5, roomNames)
        )[0]

    m = gp.Model(modelname)
    m.setParam("TimeLimit", timeLimit)

    roomNames = [r["name"] for r in rooms]
    x = var_prt(m, patients, roomNames, firstDay, lastDay, "Patient-Room Assignment")
    g = var_rt(m, roomNames, firstDay, lastDay, "is female in room")
    delta = var_prt(m, patients, roomNames, firstDay, lastDay, "transfers")
    modelVars = {"x": x, "g": g, "delta": delta}
    if useVarMrt:
        mm = var_rt(m, roomNames, firstDay, lastDay, "is male in room")
        modelVars["m"] = mm
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

    for day in range(firstDay, lastDay + 1):
        hospitalizedPatients = filterPatients([isHospitalizedOnDay(day)], patients)
        m.addConstrs(
            x.sum(pID, "*", day) == 1 for pID in getPatientIDs(hospitalizedPatients)
        )
        for r in rooms:
            if not optimizeTransfersOnly:
                m.addConstrs(
                    s[pID, r["name"], day] <= x[pID, r["name"], day]
                    for pID in filterPatients(
                        [isPrivate], hospitalizedPatients, onlyIDs=True
                    )
                )
            if useVarMrt:
                m.addConstr(
                    g[r["name"], day] + mm[r["name"], day] <= 1,
                    "room either female or male",
                )
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
        c(m, modelVars, useVarMrt, patients, rooms, firstDay, lastDay)
    transfers = delta.sum("*", "*", "*") + transfersOfCurrentPatients
    if optimizeTransfersOnly:
        m.setObjective(transfers)
        m.ModelSense = GRB.MINIMIZE
    else:
        m.ModelSense = GRB.MAXIMIZE
        privates = s.sum("*", "*", "*")
        m.setObjectiveN(
            transfers,
            1,
            priority=fPrio["ftrans"],
            weight=fWeight["ftrans"],
            name="transfers",
        )
        m.setObjectiveN(
            privates,
            0,
            priority=fPrio["fpriv"],
            weight=fWeight["fpriv"],
            name="privates",
        )

    m.setParam(GRB.Param.PoolSolutions, 100)

    m.optimize()
    assert m.Status != GRB.INFEASIBLE, "ERROR: IP_prt is infeasible"
    assert m.Status != GRB.INF_OR_UNBD, "ERROR: IP_prt is infeasible or unbounded"
    assert (
        m.SolCount != 0
    ), "ERROR: couldn't find a feasible solution in the given time limit"
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

    nObjectives = m.NumObj
    objPrios = {}
    for o in range(nObjectives):
        m.params.ObjNumber = o
        objPrios[m.ObjNName] = m.ObjNPriority

    return {
        "model_name": {firstDay: m.ModelName},
        "objective_setup": {firstDay: objPrios},
        "patient_assignments": patient_assignments,
        "transfers": daylyTransfers,
        "total_transfers": round(transfers.getValue()),
        "private_rooms": nPrivatebeds,
        "optimization_time": {firstDay: round(m.Runtime, 5)},
        "mipGap": {firstDay: mipGap},
    }
