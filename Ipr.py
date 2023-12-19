from Iprt import fix_smax


def capacity_constraint_pr(
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


def sex_separation_constraint_pr(
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
                    modelVars["x"][p, r["name"]] <= modelVars["g"][r["name"], day]
                )
            for p in filterPatients([isMale], hospitalizedPatients, onlyIDs=True):
                model.addConstr(
                    modelVars["x"][p, r["name"]] <= 1 - modelVars["g"][r["name"], day]
                )


def capacity_sex_separation_constraint_pr(
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
                    modelVars["x"][p, r["name"]]
                    for p in filterPatients(
                        [isFemale], hospitalizedPatients, onlyIDs=True
                    )
                )
                <= r["capacity"] * modelVars["g"][r["name"], day]
            )
            model.addConstr(
                gp.quicksum(
                    modelVars["x"][p, r["name"]]
                    for p in filterPatients(
                        [isMale], hospitalizedPatients, onlyIDs=True
                    )
                )
                <= r["capacity"] * (1 - modelVars["g"][r["name"], day])
            )


def single_room_constraint_pr(
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
                        modelVars["x"][q, r["name"]]
                        for q in getPatientIDs(hospitalizedPatients)
                    )
                    <= r["capacity"] + modelVars["x"][p, r["name"]]
                )


def single_room_capacity_sex_separation_constraint_pr(
    m, modelVars, useVarMrt, patients, rooms, firstDay, lastDay
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
                modelVars["x"][pID, r["name"]]
                for pID in filterPatients(
                    [isFemale], hospitalizedPatients, onlyIDs=True
                )
            )
            sumMalePatients = gp.quicksum(
                modelVars["x"][pID, r["name"]]
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

            m.addConstr(
                sumFemalePatients + sumFemalePrivatePatients
                <= r["capacity"] * modelVars["g"][r["name"], day]
            )
            m.addConstr(
                sumMalePatients + sumMalePrivatePatients
                <= r["capacity"] * (1 - modelVars["g"][r["name"], day])
            )


def var_pr(model, patients, roomNames, varName):
    from gurobipy import GRB

    return model.addVars(
        map(lambda p: p["id"], patients), roomNames, vtype=GRB.BINARY, name=varName
    )


def var_rt(model, roomNames, firstDay, lastDay, varName):
    from gurobipy import GRB

    return model.addVars(
        roomNames, range(firstDay, lastDay + 1), vtype=GRB.BINARY, name=varName
    )


def var_prt(model, patients, roomNames, firstDay, lastDay, varName):
    from gurobipy import GRB
    from filter import filterPatients, isPrivate, get_patient_IDs_with_relevant_days

    indices = [
        (p["patientID"], r, d)
        for p in get_patient_IDs_with_relevant_days(patients, firstDay, lastDay)
        for d in range(p["first_relevant_day"], p["last_relevant_day"] + 1)
        for r in roomNames
    ]
    return model.addVars(indices, vtype=GRB.BINARY, name=varName)


def forbid_transfers_of_hospitalized_patients(
    model, modelVars, patients, currentPatientAssignment, fPrio, fWeight
):
    import gurobipy as gp

    for p in patients:
        if p["id"] in currentPatientAssignment.keys():
            model.addConstr(
                modelVars["x"][p["id"], currentPatientAssignment[p["id"]]] == 1
            )
    return gp.quicksum(0 for i in range(3)), 0


def allow_transfers_of_hospitalized_patients(
    model, modelVars, patients, currentPatientAssignment, fPrio, fWeight
):
    import gurobipy as gp
    from filter import getPatientIDs

    print("at least one transfer is necessary")
    preAssignedPatientIDs = [
        pID
        for pID in list(getPatientIDs(patients))
        if pID in currentPatientAssignment.keys()
    ]
    transfers = gp.quicksum(
        modelVars["x"][pID, currentPatientAssignment[pID]]
        for pID in preAssignedPatientIDs
    )
    model.setObjectiveN(transfers, 1, priority=fPrio, weight=fWeight, name="transfers")
    return transfers, len(preAssignedPatientIDs)


def add_upper_bound_single_rooms_for_private_patients_total(
    model, patients, modelVars, lastDay, firstDay=0
):
    from analyze_instance import get_total_smax

    smaxTotal = get_total_smax(patients, nRooms, lastDay, firstDay)
    model.addConstr(modelVars["s"].sum("*", "*", "*") <= smaxTotal)
    return smaxTotal


def get_private_beds(modelVars, firstDay, lastDay):
    return {
        d: round(modelVars["s"].sum("*", "*", d).getValue())
        for d in range(firstDay, lastDay + 1)
    }


def IP(
    patients,
    firstDay,
    lastDay,
    rooms,
    currentPatientAssignment={},
    current_assignment_condition=forbid_transfers_of_hospitalized_patients,
    timeLimit=60,
    useVarMrt=False,
    modelname="O",
    fPrio={"ftrans": 0, "fpriv": 1},
    fWeight={"ftrans": -1, "fpriv": 1},
    constraints=[single_room_capacity_sex_separation_constraint_pr],
):
    import gurobipy as gp
    from gurobipy import GRB

    from filter import (
        filterPatients,
        isPrivate,
        getPatientIDs,
        isFemale,
        isMale,
        isHospitalizedOnDay,
    )
    from Iprt import fix_smax

    def get_room(modelVars, patientID, roomNames):
        return list(filter(lambda r: modelVars["x"][patientID, r].x > 0.5, roomNames))[
            0
        ]

    m = gp.Model(modelname)
    m.setParam("TimeLimit", timeLimit)

    roomNames = [r["name"] for r in rooms]
    x = var_pr(m, patients, roomNames, "patient-room assignment")
    g = var_rt(m, roomNames, firstDay, lastDay, "is female in room")
    s = var_prt(
        m,
        filterPatients([isPrivate], patients),
        roomNames,
        firstDay,
        lastDay,
        "gets private patient a single room",
    )
    modelVars = {"x": x, "g": g, "s": s}
    m.ModelSense = GRB.MAXIMIZE
    m.setObjectiveN(
        s.sum("*", "*", "*"),
        0,
        priority=fPrio["fpriv"],
        weight=fWeight["fpriv"],
        name="privates",
    )

    m.addConstrs(x.sum(pID, "*") == 1 for pID in getPatientIDs(patients))

    for day in range(firstDay, lastDay + 1):
        hospitalizedPatients = filterPatients([isHospitalizedOnDay(day)], patients)
        for r in rooms:
            for pID in filterPatients([isPrivate], hospitalizedPatients, onlyIDs=True):
                m.addConstr(s[pID, r["name"], day] <= modelVars["x"][pID, r["name"]])

    for c in constraints:
        c(m, modelVars, useVarMrt, patients, rooms, firstDay, lastDay)

    transfers, maxPossibleTransfers = current_assignment_condition(
        m,
        modelVars,
        patients,
        currentPatientAssignment,
        fPrio["ftrans"],
        fWeight["ftrans"],
    )

    m.optimize()
    if m.Status == GRB.INFEASIBLE:
        return None
    if m.Status == GRB.TIME_LIMIT and m.SolCount == 0:
        return None
    if m.Status != GRB.OPTIMAL:
        mipGap = m.Params.MIPGap
    else:
        mipGap = 0.0
    patient_assignments = {
        p["id"]: [
            {
                "start": max(firstDay, p["admission"]),
                "end": p["discharge"] - 1,
                "roomName": get_room(modelVars, p["id"], roomNames),
            }
        ]
        for p in patients
    }
    daylyTransfers = {d: 0 for d in range(firstDay, lastDay + 1)}
    daylyTransfers[firstDay] = maxPossibleTransfers - int(transfers.getValue())
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
        "private_rooms": nPrivatebeds,
        "optimization_time": {firstDay: round(m.Runtime, 5)},
        "mipGap": {firstDay: mipGap},
    }
