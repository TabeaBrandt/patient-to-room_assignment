from Iprt import IP_prt
from Iprt import (
    capacity_constraint,
    sex_separation_constraint,
    capacity_sex_separation_constraint,
    single_room_constraint,
    single_room_capacity_sex_separation_constraint,
)


def static(
    file,
    fileNameOut,
    firstDay=0,
    lastDay=364,
    timeLimit=12 * 60 * 60,
    ip_fkt=IP_prt,
    fPrio={"ftrans": 0, "fpriv": 1},
    fWeight={"ftrans": -1, "fpriv": 1},
    constraints=[],
    useVarMrt=False,
):
    import json
    import codecs
    from filter import filterPatients, isHospitalizedInInterval
    from time import time

    from Dynamic import init_result, append_result

    print(file, fileNameOut)
    startTime = time()

    with open(file + ".json") as f:
        d = json.load(f)
        rooms = d["rooms"]
    patients = filterPatients(
        [isHospitalizedInInterval(firstDay, lastDay)], d["patients"]
    )
    result = init_result()
    newResult = ip_fkt(
        patients,
        firstDay,
        lastDay,
        rooms,
        timeLimit=timeLimit,
        fPrio=fPrio,
        fWeight=fWeight,
        constraints=constraints,
        useVarMrt=useVarMrt,
    )
    endTime = time()
    if not newResult:
        newResult = {"status": "infeasible"}
    newResult["runtime"] = {firstDay: endTime - startTime}
    result = append_result(result, newResult)

    endTime = time()
    result["total_runtime"] = endTime - startTime
    with codecs.open(
        "Results/" + file + "_" + fileNameOut + ".json", "w", encoding="utf-8"
    ) as out:
        out.write(json.dumps(result, indent=4))


if __name__ == "__main__":
    from Ipr import IP, capacity_constraint_pr,sex_separation_constraint_pr
    from Iprt import IP_prt

    static(
        "2019/AU01",
        "testout",
        timeLimit=60,
        constraints=[
            capacity_constraint_pr,
            sex_separation_constraint_pr,
        ],
        useVarMrt=True,
        ip_fkt=IP,
        fPrio={"ftrans": 0, "fpriv": 0},
        fWeight={"ftrans": 0, "fpriv": 0},
    )
