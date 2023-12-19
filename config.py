from Dynamic import dynamic
from Static import static
from Ipr import (
    IP,
    capacity_constraint_pr,
    sex_separation_constraint_pr,
    single_room_constraint_pr,
    capacity_sex_separation_constraint_pr,
    single_room_capacity_sex_separation_constraint_pr,
)
from Iprt import (
    IP_prt,
    capacity_constraint,
    sex_separation_constraint,
    single_room_constraint,
    capacity_sex_separation_constraint,
    single_room_capacity_sex_separation_constraint,
    fix_smax,
    fix_smax_eq,
)

config = {
    "static": {
        "function": static,
        "parameter": {
            "timeLimit": 12 * 60 * 60,
        },
        "filename": "stc",
        "IPprt": {
            "parameter": {"ip_fkt": IP_prt},
            "filename": "prt",
            "onlyTrans": {
                "parameter": {
                    "fPrio": {"ftrans": 1, "fpriv": 1},
                    "fWeight": {"ftrans": -1, "fpriv": 0},
                },
                "sepM": {
                    "filename": "",
                    "parameter": {
                        "constraints": [
                            capacity_constraint,
                            sex_separation_constraint,
                            single_room_constraint,
                        ]
                    },
                    "useMrt": {"filename": "A", "parameter": {"useVarMrt": True}},
                    "omitMrt": {"filename": "B", "parameter": {"useVarMrt": False}},
                },
                "combiCapSex": {
                    "filename": "",
                    "parameter": {
                        "constraints": [
                            capacity_sex_separation_constraint,
                            single_room_constraint,
                        ]
                    },
                    "useMrt": {"filename": "C", "parameter": {"useVarMrt": True}},
                    "omitMrt": {"filename": "D", "parameter": {"useVarMrt": False}},
                },
                "fixSmax": {
                    "filename": "K",
                    "parameter": {
                        "constraints": [
                            capacity_sex_separation_constraint,
                            single_room_constraint,
                            fix_smax,
                        ],
                        "useVarMrt": False,
                    },
                },
                "fixSmaxEq": {
                    "filename": "L",
                    "parameter": {
                        "constraints": [
                            capacity_sex_separation_constraint,
                            single_room_constraint,
                            fix_smax_eq,
                        ],
                        "useVarMrt": False,
                    },
                },
                "fixSmaxH": {
                    "filename": "KK",
                    "parameter": {
                        "constraints": [
                            single_room_capacity_sex_separation_constraint,
                            fix_smax,
                        ],
                        "useVarMrt": False,
                    },
                },
                "fixSmaxEqH": {
                    "filename": "LL",
                    "parameter": {
                        "constraints": [
                            single_room_capacity_sex_separation_constraint,
                            fix_smax_eq,
                        ],
                        "useVarMrt": False,
                    },
                },
            },
            "minTransMaxSingle": {
                "parameter": {
                    "fPrio": {"ftrans": 1, "fpriv": 0},
                    "fWeight": {"ftrans": -1, "fpriv": 1},
                },
                "filename": "",
                "E": {
                    "filename": "E",
                    "parameter": {
                        "constraints": [
                            capacity_sex_separation_constraint,
                            single_room_constraint,
                        ]
                    },
                },
                "H": {
                    "filename": "H",
                    "parameter": {
                        "constraints": [single_room_capacity_sex_separation_constraint]
                    },
                },
            },
            "MaxSingleMinTrans": {
                "parameter": {
                    "fPrio": {"ftrans": 0, "fpriv": 1},
                    "fWeight": {"ftrans": -1, "fpriv": 1},
                },
                "filename": "",
                "F": {
                    "filename": "F",
                    "parameter": {
                        "constraints": [
                            capacity_sex_separation_constraint,
                            single_room_constraint,
                        ]
                    },
                },
                "I": {
                    "filename": "I",
                    "parameter": {
                        "constraints": [single_room_capacity_sex_separation_constraint]
                    },
                },
            },
            "aggregate": {
                "parameter": {
                    "fPrio": {"ftrans": 1, "fpriv": 1},
                    "fWeight": {"ftrans": -1, "fpriv": 2},
                },
                "filename": "",
                "G": {
                    "filename": "G",
                    "parameter": {
                        "constraints": [
                            capacity_sex_separation_constraint,
                            single_room_constraint,
                        ]
                    },
                },
                "J": {
                    "filename": "J",
                    "parameter": {
                        "constraints": [single_room_capacity_sex_separation_constraint]
                    },
                },
            },
        },
        "IPpr": {
            "parameter": {"ip_fkt": IP},
            "filename": "pr",
            "M": {
                "filename": "M",
                "parameter": {
                    "constraints": [
                        capacity_constraint_pr,
                        sex_separation_constraint_pr,
                        single_room_constraint_pr,
                    ]
                },
            },
            "N": {
                "filename": "N",
                "parameter": {
                    "constraints": [
                        capacity_sex_separation_constraint_pr,
                        single_room_constraint_pr,
                    ]
                },
            },
            "O": {
                "filename": "O",
                "parameter": {
                    "constraints": [single_room_capacity_sex_separation_constraint_pr]
                },
            },
            "P": {
                "filename": "P",
                "parameter": {
                    "constraints": [
                        single_room_capacity_sex_separation_constraint_pr,
                        fix_smax,
                    ],
                    "fWeight": {"ftrans": 0, "fpriv": 0},
                },
            },
        },
    },
    "dynamic": {
        "function": dynamic,
        "parameter": {
            "timeLimit": 60 * 60,
        },
        "filename": "dyn",
    },
}
