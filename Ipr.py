def fix_wmin(
    m, modelVars, patients, firstDay, lastDay, roommateTuples, get_pref, fPrio, fWeight, nRooms
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

    for t in range(firstDay, lastDay+1):
        hospitalizedPatients = filterPatients([isHospitalizedOnDay(t)], patients)
        females = filterPatients([isFemale], hospitalizedPatients)
        males = filterPatients([isMale], hospitalizedPatients)
        res = compute_wmin_score(hospitalizedPatients, nRooms, get_pref)
        sumPreferences = gp.quicksum(get_pref(females[i],females[j])*modelVars["y"][females[i]["id"],females[j]["id"]] for i in range(len(females)) for j in range(i+1,len(females))) + gp.quicksum(get_pref(males[i],males[j])*modelVars["y"][males[i]["id"],males[j]["id"]] for i in range(len(males)) for j in range(i+1,len(males))) 
        m.addConstr(
            sumPreferences
            <= res
        )

def optimize_preferences(
    m, modelVars, patients, firstDay, lastDay, roommateTuples, get_pref, fPrio, fWeight, nRooms
):
    import gurobipy as gp
    from filter import (
        filterPatients,
        isFemale,
        isMale,
        isPrivate,
        isHospitalizedOnDay,
    )
    preferenceObj = gp.quicksum(get_length_of_common_stay(p,q,firstDay)*get_pref(p,q)*modelVars["y"][p["id"],q["id"]] for (p,q) in roommateTuples)

    m.setObjectiveN( # Link y to objective
        preferenceObj,
        0,
        priority=fPrio["fpref"],
        weight=fWeight["fpref"],
        name="preferencs",
    )

def single_room_capacity_sex_separation_constraint_pr(
    m, modelVars, patients, rooms, firstDay, lastDay, currentPatientAssignment
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

    #print("at least one transfer is necessary")
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

def get_private_beds(modelVars, firstDay, lastDay):
    return {
        d: round(modelVars["s"].sum("*", "*", d).getValue())
        for d in range(firstDay, lastDay + 1)
    }

def are_potential_roommates(p,q):
    if p["sex"] != q["sex"]:
        return False
    if set(range(p["admission"],p["discharge"])).intersection(range(q["admission"],q["discharge"])):
        return True
    return False

def weighted_age_pref(p,q,rounding=2):
    return round((max(p['age'],q['age'])+1)/(min(p['age'],q['age'])+1)-1,rounding)

def pre_post_surgery_pref(p,q,k=2):
    return int(not(abs(p['admission']-q['admission']) >= k))

def age_classes_pref(p,q,k=10):
    return int(not int(p['age']/k) == int(q['age']/k))

def absolut_age_difference_pref(p,q,k=10):
    return int(abs(p['age']-q['age']))

def bounded_age_difference_pref(p,q,k=10):
    return int(abs(p['age']-q['age']) > k)

def get_length_of_common_stay(p,q,firstDay):
    return min(p["discharge"],q["discharge"]) - max(p["admission"],q["admission"])
    

def IP(
    patients,
    firstDay,
    lastDay,
    rooms,
    currentPatientAssignment={},
    current_assignment_condition=forbid_transfers_of_hospitalized_patients,
    timeLimit=60,
    modelname="O",
    fPrio={"ftrans": 0, "fpriv": 1,"fpref": -1},
    fWeight={"ftrans": -1, "fpriv": 1, "fpref": -1},
    constraints=[single_room_capacity_sex_separation_constraint_pr],
    roommates=True,
    preference_setup=[optimize_preferences],
    get_pref=weighted_age_pref,
):
    import gurobipy as gp
    from gurobipy import GRB

    from filter import (
        filterPatients,
        isPrivate,
        getPatientIDs,
        isHospitalizedOnDay,
    )

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
    
    if roommates:
        np = len(patients)
        roommateTuples = [ (patients[i], patients[j]) for i in range(np) for j in range(i+1,np) if are_potential_roommates(patients[i],patients[j]) ]
        roommateIDtuples = [(p["id"],q["id"]) for (p,q) in roommateTuples]
        modelVars["y"] = m.addVars(roommateIDtuples, vtype=GRB.BINARY, name='roommates')
        m.addConstrs(modelVars["y"][pID,qID] >= modelVars["x"][pID,rName] + modelVars["x"][qID,rName] -1 for (pID,qID) in roommateIDtuples for rName in roomNames)
        for c in preference_setup:
            c(m, modelVars, patients, firstDay, lastDay, roommateTuples,get_pref,fPrio, fWeight, len(rooms))
        
    m.ModelSense = GRB.MAXIMIZE

    m.addConstrs(x.sum(pID, "*") == 1 for pID in getPatientIDs(patients))

    for day in range(firstDay, lastDay + 1):
        hospitalizedPatients = filterPatients([isHospitalizedOnDay(day)], patients)
        for r in rooms:
            for pID in filterPatients([isPrivate], hospitalizedPatients, onlyIDs=True):
                m.addConstr(s[pID, r["name"], day] <= modelVars["x"][pID, r["name"]])

    for c in constraints:
        c(m, modelVars, patients, rooms, firstDay, lastDay,currentPatientAssignment)

    transfers, maxPossibleTransfers = current_assignment_condition(
        m,
        modelVars,
        patients,
        currentPatientAssignment,
        fPrio["ftrans"],
        fWeight["ftrans"],
    )

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
    allScores = {}
    if roommates:
        for day in range(firstDay, lastDay+1):
            hospitalizedPatients = filterPatients([isHospitalizedOnDay(day)], patients)
            roommatescore = []
            for p in hospitalizedPatients:
                for q in hospitalizedPatients:
                    if p['id'] != q['id'] and are_potential_roommates(p,q):
                        if (q['id'],p['id']) in modelVars["y"].keys(): continue
                        if modelVars["y"][p['id'],q['id']].x > 0.99:
                            roommatescore.append(get_pref(p,q))
            allScores[day] = sum(roommatescore)
    else: roommatescore = None
    return {
        "model_name": {firstDay: [m.ModelName]},
        "status": {firstDay: [m.Status]},
        "objective_setup": {firstDay: [objPrios]},
        "patient_assignments": patient_assignments,
        "transfers": daylyTransfers,
        "private_rooms": nPrivatebeds,
        "optimization_time": {firstDay: [round(m.Runtime, 5)]},
        "mipGap": {firstDay: mipGap},
        "roommatescore": allScores,
    }
