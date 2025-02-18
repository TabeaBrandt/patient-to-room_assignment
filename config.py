from Dynamic import dynamic
from Static import static
from Ipr import (
    IP,
    single_room_capacity_sex_separation_constraint_pr,
    weighted_age_pref,
    age_classes_pref,
    absolut_age_difference_pref,
    bounded_age_difference_pref,
    pre_post_surgery_pref,
    fix_wmin,
    optimize_preferences,
)
from Iprt import (
    IP_prt,
    single_room_capacity_sex_separation_constraint,
    fix_smax,
    fix_wmin_prt,
    optimize_preferences_prt,
    optimize_smax,
)

config = {
    "static":{
        "function": static,
        "parameter": {
            "timeLimit": 60*60*4,
        },
        "filename": "stc",
        "S":{
            "parameter":{
                "roommates": True,
                "ip_fkt": IP_prt,
                "constraints": [single_room_capacity_sex_separation_constraint,fix_smax],
                "preference_setup": [fix_wmin_prt],
                "fPrio": {"ftrans": 0, "fpriv": 1, "fpref": 2},
            },
            "filename": "S",
            "weightedR":{
                "parameter": {
                    "get_pref": weighted_age_pref,
                },
                "filename": "weighted_age_score",
            },
            "boundedR":{
                "parameter": {
                    "get_pref": bounded_age_difference_pref,
                },
                "filename": "bounded_age_difference",
            },
        },
        "R":{
            "parameter":{
                "roommates": True,
                "ip_fkt": IP_prt,
                "constraints": [single_room_capacity_sex_separation_constraint,fix_smax],
                "preference_setup": [optimize_preferences_prt],
                "fPrio": {"ftrans": 0, "fpriv": 1, "fpref": 2},
            },
            "filename": "R",
            "weightedR":{
                "parameter": {
                    "get_pref": weighted_age_pref,
                },
                "filename": "weighted_age_score",
            },
            "boundedR":{
                "parameter": {
                    "get_pref": bounded_age_difference_pref,
                },
                "filename": "bounded_age_difference",
            },
        },
        "Q":{
            "parameter":{
                "roommates": True,
                "ip_fkt": IP_prt,
                "constraints": [single_room_capacity_sex_separation_constraint],
                "preference_setup": [optimize_preferences_prt,optimize_smax],
                "fPrio": {"ftrans": 2, "fpriv": 1, "fpref": 0},
            },
            "filename": "Q",
            "weightedQ":{
                "parameter": {
                    "get_pref": weighted_age_pref,
                },
                "filename": "weighted_age_score",
            },
            "boundedQ":{
                "parameter": {
                    "get_pref": bounded_age_difference_pref,
                },
                "filename": "bounded_age_difference",
            },
        },
        "T":{
            "parameter":{
                "roommates": True,
                "ip_fkt": IP,
                "constraints": [single_room_capacity_sex_separation_constraint_pr],
                "preference_setup": [optimize_preferences,optimize_smax],
            },
            "filename": "T",
            "weightedT":{
                "parameter": {
                    "get_pref": weighted_age_pref,
                },
                "filename": "weighted_age_score",
            },
            "boundedT":{
                "parameter": {
                    "get_pref": bounded_age_difference_pref,
                },
                "filename": "bounded_age_difference",
            },
        },
        "U":{
            "parameter":{
                "roommates": True,
                "ip_fkt": IP,
                "constraints": [single_room_capacity_sex_separation_constraint_pr,fix_smax],
                "preference_setup": [optimize_preferences],
            },
            "filename": "U",
            "weightedU":{
                "parameter": {
                    "get_pref": weighted_age_pref,
                },
                "filename": "weighted_age_score",
            },
            "boundedU":{
                "parameter": {
                    "get_pref": bounded_age_difference_pref,
                },
                "filename": "bounded_age_difference",
            },
        },
        "V":{
            "parameter":{
                "roommates": True,
                "ip_fkt": IP,
                "constraints": [single_room_capacity_sex_separation_constraint_pr,fix_smax],
                "preference_setup": [fix_wmin],
                "get_pref": weighted_age_pref,
            },
            "filename": "Va",
            "weightedVa":{
                "parameter": {
                    "get_pref": weighted_age_pref,
                },
                "filename": "weighted_age_score",
            },
            "boundedVa":{
                "parameter": {
                    "get_pref": bounded_age_difference_pref,
                },
                "filename": "bounded_age_difference",
            },
        },
    },
    "dynamic": {
        "function": dynamic,
        "parameter": {
            "timeLimit": 60 * 60,
        },
        "filename": "dyn_U",
        "noRoomies":{
            "parameter": {
                "roommates": False,
            },
            "filename": "no_preferences",
        },
        "weightedRoomies":{
            "parameter": {
                "roommates": True,
                "get_pref": weighted_age_pref,
            },
            "filename": "weighted_age_score",
        },
        "ageClassRoomies":{
            "parameter": {
                "roommates": True,
                "get_pref": age_classes_pref,
            },
            "filename": "age_classes",
        },
        "absoluteAgeRoomies":{
            "parameter": {
                "roommates": True,
                "get_pref": absolut_age_difference_pref,
            },
            "filename": "absolut_age_difference",
        },
        "boundedAgeRoomies":{
            "parameter": {
                "roommates": True,
                "get_pref": bounded_age_difference_pref,
            },
            "filename": "bounded_age_difference",
        },
        "prepostsurgery":{
            "parameter": {
                "roommates": True,
                "get_pref": pre_post_surgery_pref,
            },
            "filename": "pre_post_surgery",
        },
    },
}
