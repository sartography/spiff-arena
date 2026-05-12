import json

from collections import namedtuple


TestCov = namedtuple("TestCov", ["all", "completed", "missing"])
Tally = namedtuple("Tally", ["completed", "all", "percent"])
CovTally = namedtuple("CovTally", ["result", "breakdown"])

def _embedded_subprocess_ids(spec, subprocess_specs, seen=None):
    if seen is None:
        seen = set()
    embedded = set()
    for task_spec in spec["task_specs"].values():
        if task_spec.get("typename") != "SubWorkflowTask":
            continue
        subprocess_id = task_spec.get("spec")
        if not subprocess_id or subprocess_id in seen:
            continue
        subprocess_spec = subprocess_specs.get(subprocess_id)
        if not subprocess_spec:
            continue
        seen.add(subprocess_id)
        embedded.add(subprocess_id)
        embedded.update(_embedded_subprocess_ids(subprocess_spec, subprocess_specs, seen))
    return embedded

def _task_ids(spec, subprocess_specs, seen=None):
    if seen is None:
        seen = set()
    ids = {
        task_id
        for task_id, task_spec in spec["task_specs"].items()
        if task_spec.get("bpmn_id")
    }
    for subprocess_id in _embedded_subprocess_ids(spec, subprocess_specs, seen):
        ids.update(_task_ids(subprocess_specs[subprocess_id], subprocess_specs, seen))
    return ids

def _embedded_subprocess_owners(specs):
    owners = {}
    for owner_id, spec_json in specs.items():
        specs_dct = json.loads(spec_json)
        subprocess_specs = specs_dct.get("subprocess_specs", {})
        for subprocess_id in _embedded_subprocess_ids(specs_dct["spec"], subprocess_specs):
            owners[subprocess_id] = owner_id
    return owners

def cov_tasks(test_cases, embedded_subprocess_owners=None):
    if embedded_subprocess_owners is None:
        embedded_subprocess_owners = {}
    for test_case in test_cases:
        state = test_case.state
        coverage_spec_id = getattr(test_case, "coverage_spec_id", None)
        if coverage_spec_id:
            for _, task in state["tasks"].items():
                if task["state"] == 64:
                    yield coverage_spec_id, task["task_spec"]
        for _, sp in state["subprocesses"].items():
            id = sp["spec"]
            id = embedded_subprocess_owners.get(id, id)
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
    embedded_subprocess_owners = _embedded_subprocess_owners(ctx.specs)
    for id, task_id in cov_tasks(ctx.test_cases, embedded_subprocess_owners):
        if id not in completed:
            completed[id] = set()
        completed[id].add(task_id)
    for id, spec in ctx.specs.items():
        if id not in completed:
            completed[id] = set()
        specs = json.loads(spec)
        all[id] = _task_ids(specs["spec"], specs.get("subprocess_specs", {}))
        completed[id] &= all[id]
        missing[id] = all[id] - completed[id]

    cov = TestCov(all, completed, missing)
    return cov, tally(cov) 
