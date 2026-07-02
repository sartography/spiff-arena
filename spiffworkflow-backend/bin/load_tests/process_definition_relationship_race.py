#!/usr/bin/env python3
"""Reproduce the BPMN process-definition relationship insert race.

Run from spiffworkflow-backend against a configured local database:

    uv run python bin/load_tests/process_definition_relationship_race.py --mode both

`--mode old` intentionally uses the former check-then-add pattern with a barrier
between the read and insert. It should reproduce a duplicate-key failure.

`--mode fixed` uses BpmnProcessDefinitionRelationshipModel.insert_or_update_record.
It should complete without errors and leave exactly one relationship row.
"""

# ruff: noqa: E402,I001

from __future__ import annotations

import argparse
import concurrent.futures
import os
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("SPIFFWORKFLOW_BACKEND_RUN_BACKGROUND_SCHEDULER_IN_CREATE_APP", "false")
os.environ.setdefault("SPIFFWORKFLOW_BACKEND_ENV", "local_development")
os.environ.setdefault("FLASK_SESSION_SECRET_KEY", "relationship-race-local-dev")
os.environ.setdefault("SPIFFWORKFLOW_BACKEND_FAIL_ON_INVALID_PROCESS_MODELS", "false")

BACKEND_DIR = Path(__file__).resolve().parents[2]
ARENA_DIR = BACKEND_DIR.parent
SAMPLE_PROCESS_MODELS_DIR = ARENA_DIR / "sample-process-models"
if not SAMPLE_PROCESS_MODELS_DIR.is_dir():
    SAMPLE_PROCESS_MODELS_DIR = ARENA_DIR.parent / "sample-process-models"
os.environ.setdefault("SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR", str(SAMPLE_PROCESS_MODELS_DIR))

from flask import Flask  # noqa: E402

from spiffworkflow_backend import create_app  # noqa: E402
from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel  # noqa: E402
from spiffworkflow_backend.models.bpmn_process_definition_relationship import (  # noqa: E402
    BpmnProcessDefinitionRelationshipModel,
)
from spiffworkflow_backend.models.db import db  # noqa: E402


@dataclass
class WorkerResult:
    worker_index: int
    ok: bool
    error: str | None = None


@dataclass
class RaceRows:
    parent_id: int
    child_id: int


def create_race_rows(run_id: str) -> RaceRows:
    parent_definition = BpmnProcessDefinitionModel(
        single_process_hash=f"{run_id}-parent-single",
        full_process_model_hash=f"{run_id}-parent-full",
        bpmn_identifier=f"{run_id}_parent",
        bpmn_name="Relationship Race Parent",
        properties_json={},
        bpmn_version_control_type="race",
        bpmn_version_control_identifier=run_id,
    )
    child_definition = BpmnProcessDefinitionModel(
        single_process_hash=f"{run_id}-child-single",
        full_process_model_hash=None,
        bpmn_identifier=f"{run_id}_child",
        bpmn_name="Relationship Race Child",
        properties_json={},
        bpmn_version_control_type="race",
        bpmn_version_control_identifier=run_id,
    )
    db.session.add_all([parent_definition, child_definition])
    db.session.commit()
    return RaceRows(parent_id=parent_definition.id, child_id=child_definition.id)


def relationship_count(parent_id: int, child_id: int) -> int:
    return BpmnProcessDefinitionRelationshipModel.query.filter_by(
        bpmn_process_definition_parent_id=parent_id,
        bpmn_process_definition_child_id=child_id,
    ).count()


def delete_relationship(parent_id: int, child_id: int) -> None:
    BpmnProcessDefinitionRelationshipModel.query.filter_by(
        bpmn_process_definition_parent_id=parent_id,
        bpmn_process_definition_child_id=child_id,
    ).delete()
    db.session.commit()


def delete_race_rows(rows: RaceRows) -> None:
    delete_relationship(rows.parent_id, rows.child_id)
    BpmnProcessDefinitionModel.query.filter(BpmnProcessDefinitionModel.id.in_([rows.parent_id, rows.child_id])).delete(
        synchronize_session=False
    )
    db.session.commit()


def old_check_then_insert_worker(app: Flask, rows: RaceRows, barrier: threading.Barrier, worker_index: int) -> WorkerResult:
    with app.app_context():
        try:
            existing_relationship = BpmnProcessDefinitionRelationshipModel.query.filter_by(
                bpmn_process_definition_parent_id=rows.parent_id,
                bpmn_process_definition_child_id=rows.child_id,
            ).first()
            barrier.wait()
            if existing_relationship is None:
                db.session.add(
                    BpmnProcessDefinitionRelationshipModel(
                        bpmn_process_definition_parent_id=rows.parent_id,
                        bpmn_process_definition_child_id=rows.child_id,
                    )
                )
            db.session.commit()
            return WorkerResult(worker_index=worker_index, ok=True)
        except Exception as exception:
            db.session.rollback()
            return WorkerResult(worker_index=worker_index, ok=False, error=repr(exception))
        finally:
            db.session.remove()


def fixed_insert_worker(app: Flask, rows: RaceRows, barrier: threading.Barrier, worker_index: int) -> WorkerResult:
    with app.app_context():
        try:
            barrier.wait()
            BpmnProcessDefinitionRelationshipModel.insert_or_update_record(rows.parent_id, rows.child_id)
            db.session.commit()
            return WorkerResult(worker_index=worker_index, ok=True)
        except Exception as exception:
            db.session.rollback()
            return WorkerResult(worker_index=worker_index, ok=False, error=repr(exception))
        finally:
            db.session.remove()


def run_workers(app: Flask, rows: RaceRows, workers: int, mode: str) -> list[WorkerResult]:
    barrier = threading.Barrier(workers)
    worker = old_check_then_insert_worker if mode == "old" else fixed_insert_worker
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(worker, app, rows, barrier, index) for index in range(workers)]
        return [future.result() for future in concurrent.futures.as_completed(futures)]


def run_mode(app: Flask, rows: RaceRows, workers: int, mode: str) -> bool:
    with app.app_context():
        delete_relationship(rows.parent_id, rows.child_id)

    results = run_workers(app, rows, workers, mode)

    with app.app_context():
        count = relationship_count(rows.parent_id, rows.child_id)

    failures = [result for result in results if not result.ok]
    print(f"{mode}: {len(results) - len(failures)}/{len(results)} workers succeeded; relationship_count={count}")
    for failure in failures:
        print(f"{mode}: worker {failure.worker_index} failed: {failure.error}")

    if mode == "old":
        reproduced = len(failures) > 0 and count == 1
        print(f"old: {'reproduced duplicate-key race' if reproduced else 'did not reproduce duplicate-key race'}")
        return reproduced

    passed = not failures and count == 1
    print(f"fixed: {'passed' if passed else 'failed'}")
    return passed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["old", "fixed", "both"], default="both")
    parser.add_argument("--workers", type=int, default=2, help="Number of concurrent workers. Use at least 2.")
    parser.add_argument("--keep-rows", action="store_true", help="Leave generated definition rows in the database.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.workers < 2:
        raise RuntimeError("--workers must be at least 2")

    connexion_app = create_app()
    app = connexion_app.app
    run_id = f"relationship_race_{uuid.uuid4().hex}"

    with app.app_context():
        rows = create_race_rows(run_id)
        print(f"created race rows: parent_id={rows.parent_id}, child_id={rows.child_id}")

    try:
        if args.mode == "both":
            old_reproduced = run_mode(app, rows, args.workers, "old")
            fixed_passed = run_mode(app, rows, args.workers, "fixed")
            return 0 if old_reproduced and fixed_passed else 1

        passed = run_mode(app, rows, args.workers, args.mode)
        return 0 if passed else 1
    finally:
        if not args.keep_rows:
            with app.app_context():
                delete_race_rows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
