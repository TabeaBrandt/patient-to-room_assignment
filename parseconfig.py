#!/usr/bin/env python


firstNotNoneElement = lambda l: next((e for e in l if e is not None), None)

configLabels = {
    "filename": lambda node, leaf: (node + "_" + leaf) if node else leaf,
    "function": lambda node, leaf: leaf if leaf else node,
    "enabled": lambda node, leaf: firstNotNoneElement([leaf, node, True]),
    "parameter": lambda node, leaf: (dict(node, **leaf) if node else leaf)
    if leaf
    else (node if node else {}),
}


def node2Calls(node):
    def getChildren(node):
        return list(filter(lambda c: c not in configLabels.keys(), node.keys()))

    def updateLeaf(leaf, node):
        return dict(
            leaf,
            **{
                k: configLabels[k](node.get(k), leaf.get(k))
                for k in configLabels.keys()
            }
        )

    if set(node.keys()) <= set(configLabels.keys()):  # node is leaf
        return [{k: node.get(k) for k in configLabels.keys()}]
    return [
        updateLeaf(leaf, node)
        for child in getChildren(node)
        for leaf in node2Calls(node[child])
    ]


def parse_config(filename):
    import json

    with open(filename) as file:
        data = json.load(file)
    return node2Calls(data)


def call_to_string(call, filename):
    def map_function_pointer(parameter):
        return {
            k: parameter[k].__name__
            if type(parameter[k]).__name__ == "function"
            else parameter[k]
            for k in parameter.keys()
        }

    def parameter_to_string(parameter):
        return ", ".join([str(k) + "=" + str(parameter[k]) for k in parameter.keys()])

    return (
        "python -c '"
        + call["function"].__name__
        + "("
        + filename
        + ","
        + call["filename"]
        + ","
        + parameter_to_string(map_function_pointer(call["parameter"]))
        + ")'"
    )


if __name__ == "__main__":
    from pprint import pprint
    from config import *
    import sys

    instance = sys.argv[1] + "/" + sys.argv[2]
    a = int(sys.argv[3])

    calls = node2Calls(config)
    if a < len(calls):
        c = calls[a]
        pprint(c)
        if c["enabled"]:
            #            with open('Results/logs/'+instance+'_'+c['filename']+'.log', 'w') as sys.stdout:
            #                with open('Results/logs/'+instance+'_'+c['filename']+'.err', 'w') as sys.stderr:
            c["function"](instance, c["filename"], **c["parameter"])
