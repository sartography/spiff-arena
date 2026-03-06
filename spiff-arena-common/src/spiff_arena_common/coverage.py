import json

from collections import namedtuple


TestCov = namedtuple("TestCov", ["all", "completed", "missing"])
Tally = namedtuple("Tally", ["completed", "all", "percent"])
CovTally = namedtuple("CovTally", ["result", "breakdown"])

def cov_tasks(states):
    for state in states:
        for _, sp in state["subprocesses"].items():
            id = sp["spec"]
            for _, task in sp["tasks"].items():
                if task["state"] == 64:
                    yield id, task["task_spec"]

def tally(cov):
    completed = 0
    all = 0
    breakdown = {}
    for id in cov.all:
        c = len(cov.completed[id])
        a = len(cov.all[id])
        breakdown[id] = Tally(c, a, c / a * 100)
        completed += c
        all += a
    result = Tally(completed, all, completed / all * 100)
    return CovTally(result, breakdown)

def task_coverage(ctx):
    states = [t.state for t in ctx.test_cases]
    all = {}
    completed = {}
    missing = {}
    for id, task_id in cov_tasks(states):
        if id not in completed:
            completed[id] = set()
        completed[id].add(task_id)
    for id, spec in ctx.specs.items():
        if id not in completed:
            completed[id] = set()
        spec = json.loads(spec)["spec"]
        all[id] = set([t for t in spec["task_specs"]])
        missing[id] = all[id] - completed[id]

    cov = TestCov(all, completed, missing)
    return cov, tally(cov) 
