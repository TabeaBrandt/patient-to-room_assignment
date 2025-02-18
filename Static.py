from Iprt import IP_prt
from Iprt import (
    single_room_capacity_sex_separation_constraint,
    fix_smax,
    optimize_preferences_prt,
    fix_wmin_prt,
    optimize_smax,
)
from Ipr import single_room_capacity_sex_separation_constraint_pr, fix_wmin, weighted_age_pref, are_potential_roommates, pre_post_surgery_pref, optimize_preferences, bounded_age_difference_pref


def static(
    file,
    fileNameOut,
    firstDay=0,
    lastDay=364,
    timeLimit=12 * 60 * 60,
    ip_fkt=IP_prt,
    fPrio={"ftrans": 0, "fpriv": 1, "fpref": -1},
    fWeight={"ftrans": -1, "fpriv": 1, "fpref": -1},
    constraints=[],
    preference_setup=[],
    get_pref=weighted_age_pref,
    roommates=True,
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
    result = ip_fkt(
        patients,
        firstDay,
        lastDay,
        rooms,
        timeLimit=timeLimit,
        fPrio=fPrio,
        fWeight=fWeight,
        constraints=constraints,
        preference_setup=preference_setup,
        get_pref=get_pref,
        roommates=roommates,
    )
    endTime = time()
    result ["runtime"] = {firstDay: endTime - startTime}
    endTime = time()
    result["total_runtime"] = endTime - startTime
    with codecs.open(
        "Results/" + file + "_" + fileNameOut + ".json", "w", encoding="utf-8"
    ) as out:
        out.write(json.dumps(result, indent=4))


if __name__ == "__main__":
    from Ipr import IP
    from Iprt import IP_prt

    static(
        "instances/load_50/1",
        "testout_fix",
        timeLimit=20,
        constraints=[
           single_room_capacity_sex_separation_constraint,
           fix_smax,
        ],
        ip_fkt=IP_prt,
        roommates=True,
        preference_setup=[optimize_preferences_prt,],
#        preference_setup=[fix_wmin_prt],
        get_pref=bounded_age_difference_pref,
        fPrio={"ftrans": 0, "fpriv": 1, "fpref": 2},
    )
