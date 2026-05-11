import json

from collections import namedtuple


TestCov = namedtuple("TestCov", ["all", "completed", "missing"])
Tally = namedtuple("Tally", ["completed", "all", "percent"])
CovTally = namedtuple("CovTally", ["result", "breakdown"])

def cov_tasks(test_cases):
    for test_case in test_cases:
        state = test_case.state
        coverage_spec_id = getattr(test_case, "coverage_spec_id", None)
        if coverage_spec_id:
            for _, task in state["tasks"].items():
                if task["state"] == 64:
                    yield coverage_spec_id, task["task_spec"]
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
        completed_tasks = cov.completed[id] & cov.all[id]
        c = len(completed_tasks)
        a = len(cov.all[id])
        breakdown[id] = Tally(c, a, c / a * 100)
        completed += c
        all += a
    result = Tally(completed, all, completed / all * 100)
    return CovTally(result, breakdown)

def task_coverage(ctx):
    all = {}
    completed = {}
    missing = {}
    for id, task_id in cov_tasks(ctx.test_cases):
        if id not in completed:
            completed[id] = set()
        completed[id].add(task_id)
    for id, spec in ctx.specs.items():
        if id not in completed:
            completed[id] = set()
        spec = json.loads(spec)["spec"]
        all[id] = set(
            task_id
            for task_id, task_spec in spec["task_specs"].items()
            if task_spec.get("bpmn_id")
        )
        completed[id] &= all[id]
        missing[id] = all[id] - completed[id]

    cov = TestCov(all, completed, missing)
    return cov, tally(cov) 
