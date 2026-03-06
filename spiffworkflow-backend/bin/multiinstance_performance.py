"""Performance test measuring key operations in spiff-arena multiinstance execution.

Standalone script - run with: uv run python bin/multiinstance_performance.py

Measures:
1. SpiffTask.run() - Pure SpiffWorkflow execution
2. update_task_model() - BPMN process updates (includes workflow data serialization)
3. find_or_create_task_model() - Task model lookup and creation
4. Other - Unaccounted framework overhead
"""

import glob as glob_module
import os
import shutil
import tempfile
import time
from pathlib import Path

from flask import current_app
from SpiffWorkflow.task import Task as SpiffTask

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.bpmn_process_service import BpmnProcessService
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceQueueService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.spec_file_service import SpecFileService
from spiffworkflow_backend.services.task_service import TaskService
from spiffworkflow_backend.services.user_service import UserService


def load_test_spec(process_model_id: str, process_model_source_directory: str) -> ProcessModelInfo:
    """Load a BPMN process model from a directory in tests/data."""
    spec = ProcessModelInfo(
        id=process_model_id,
        display_name=process_model_id,
        description="",
    )
    ProcessModelService.add_process_model(spec)

    bpmn_file_name_with_extension = os.path.basename(process_model_id) + ".bpmn"

    file_glob = os.path.join(current_app.instance_path, "..", "..", "tests", "data", process_model_source_directory, "*.*")

    files = sorted(glob_module.glob(file_glob))
    if len(files) == 0:
        raise Exception(f"Could not find any files with file_glob: {file_glob}")

    all_references = []
    for file_path in files:
        if os.path.isdir(file_path):
            continue
        filename = os.path.basename(file_path)
        is_primary = filename.lower() == bpmn_file_name_with_extension
        with open(file_path, "rb") as f:
            data = f.read()
        _, new_references = SpecFileService.update_file(
            process_model_info=spec, file_name=filename, binary_data=data, update_process_cache_only=True
        )
        all_references += new_references
        if is_primary:
            spec.primary_process_id = new_references[0].identifier
            spec.primary_file_name = filename
            ProcessModelService.save_process_model(spec)
    for ref in all_references:
        SpecFileService.update_caches_except_process(ref)
    db.session.commit()
    return spec


class BottleneckInstrumenter:
    """Instrument key operations in task processing."""

    def __init__(self):
        self.spiff_run_count = 0
        self.update_task_model_count = 0
        self.find_or_create_count = 0

        self.spiff_run_time = 0.0
        self.update_task_model_time = 0.0
        self.find_or_create_time = 0.0

        self.original_spiff_run = SpiffTask.run
        self.original_update_task_model = TaskService.update_task_model
        self.original_find_or_create = TaskService.find_or_create_task_model_from_spiff_task

        self.results: list[dict] = []

    def install(self):
        instrumenter = self

        def instrumented_spiff_run(spiff_task_self):
            start = time.time()
            result = instrumenter.original_spiff_run(spiff_task_self)
            instrumenter.spiff_run_time += time.time() - start
            instrumenter.spiff_run_count += 1
            return result

        def instrumented_update_task_model(service_self, task_model, spiff_task):
            start = time.time()
            result = instrumenter.original_update_task_model(service_self, task_model, spiff_task)
            instrumenter.update_task_model_time += time.time() - start
            instrumenter.update_task_model_count += 1
            return result

        def instrumented_find_or_create(service_self, spiff_task):
            start = time.time()
            result = instrumenter.original_find_or_create(service_self, spiff_task)
            instrumenter.find_or_create_time += time.time() - start
            instrumenter.find_or_create_count += 1
            return result

        SpiffTask.run = instrumented_spiff_run
        TaskService.update_task_model = instrumented_update_task_model
        TaskService.find_or_create_task_model_from_spiff_task = instrumented_find_or_create

    def uninstall(self):
        SpiffTask.run = self.original_spiff_run
        TaskService.update_task_model = self.original_update_task_model
        TaskService.find_or_create_task_model_from_spiff_task = self.original_find_or_create

    def reset(self):
        self.spiff_run_count = 0
        self.update_task_model_count = 0
        self.find_or_create_count = 0
        self.spiff_run_time = 0.0
        self.update_task_model_time = 0.0
        self.find_or_create_time = 0.0

    def record(self, loop_count: int, total_time: float):
        self.results.append(
            {
                "loop_count": loop_count,
                "total_time": total_time,
                "spiff_run_time": self.spiff_run_time,
                "spiff_run_count": self.spiff_run_count,
                "update_task_time": self.update_task_model_time,
                "update_task_count": self.update_task_model_count,
                "find_create_time": self.find_or_create_time,
                "find_create_count": self.find_or_create_count,
            }
        )
        print(f"  {loop_count} items: {total_time:.2f}s total")

    def print_summary(self):
        if not self.results:
            return

        print("\n" + "=" * 120)
        print("PERFORMANCE SUMMARY - Time per Operation")
        print("=" * 120)

        print(
            f"{'Items':<8} {'Total':>8}   {'SpiffTask.run()':>28}   {'update_task_model()':>28}   "
            f"{'find_or_create()':>28}   {'Other':>16}"
        )
        print(
            f"{'':8} {'(sec)':>8}   {'Calls':>7} {'Time':>7} {'%':>5} {'ms':>6}   "
            f"{'Calls':>7} {'Time':>7} {'%':>5} {'ms':>6}   "
            f"{'Calls':>7} {'Time':>7} {'%':>5} {'ms':>6}   {'Time':>7} {'%':>5}"
        )
        print("-" * 120)

        for r in self.results:
            total = r["total_time"]

            spiff_ms = (r["spiff_run_time"] / r["spiff_run_count"] * 1000) if r["spiff_run_count"] > 0 else 0
            spiff_pct = (r["spiff_run_time"] / total * 100) if total > 0 else 0

            task_ms = (r["update_task_time"] / r["update_task_count"] * 1000) if r["update_task_count"] > 0 else 0
            task_pct = (r["update_task_time"] / total * 100) if total > 0 else 0

            find_ms = (r["find_create_time"] / r["find_create_count"] * 1000) if r["find_create_count"] > 0 else 0
            find_pct = (r["find_create_time"] / total * 100) if total > 0 else 0

            other_time = total - r["spiff_run_time"] - r["update_task_time"] - r["find_create_time"]
            other_pct = (other_time / total * 100) if total > 0 else 0

            print(
                f"{r['loop_count']:<8} {total:>8.2f}   "
                f"{r['spiff_run_count']:>7} {r['spiff_run_time']:>7.2f} {spiff_pct:>5.1f} {spiff_ms:>6.2f}   "
                f"{r['update_task_count']:>7} {r['update_task_time']:>7.2f} {task_pct:>5.1f} {task_ms:>6.2f}   "
                f"{r['find_create_count']:>7} {r['find_create_time']:>7.2f} {find_pct:>5.1f} {find_ms:>6.2f}   "
                f"{other_time:>7.2f} {other_pct:>5.1f}"
            )

        print("=" * 120)

        if len(self.results) >= 2:
            baseline = self.results[0]
            print(f"\nScaling Analysis (vs {baseline['loop_count']} items baseline):")
            print(
                f"{'Items':<8} {'Expected':>10} {'Total':>10} {'SpiffTask':>10} {'update_task':>12} "
                f"{'find_create':>12} {'Other':>10}"
            )
            print("-" * 74)

            for r in self.results[1:]:
                expected = r["loop_count"] / baseline["loop_count"]
                total_scale = r["total_time"] / baseline["total_time"] if baseline["total_time"] > 0 else 0
                spiff_scale = r["spiff_run_time"] / baseline["spiff_run_time"] if baseline["spiff_run_time"] > 0 else 0
                task_scale = r["update_task_time"] / baseline["update_task_time"] if baseline["update_task_time"] > 0 else 0
                find_scale = r["find_create_time"] / baseline["find_create_time"] if baseline["find_create_time"] > 0 else 0

                baseline_other = (
                    baseline["total_time"]
                    - baseline["spiff_run_time"]
                    - baseline["update_task_time"]
                    - baseline["find_create_time"]
                )
                current_other = r["total_time"] - r["spiff_run_time"] - r["update_task_time"] - r["find_create_time"]
                other_scale = current_other / baseline_other if baseline_other > 0 else 0

                print(
                    f"{r['loop_count']:<8} {expected:>9.1f}x {total_scale:>9.1f}x {spiff_scale:>9.1f}x "
                    f"{task_scale:>11.1f}x {find_scale:>11.1f}x {other_scale:>9.1f}x"
                )

        print("\n")


def run_single_test(instrumenter: BottleneckInstrumenter, loop_count: int):
    """Run a single performance test for the given loop count."""
    test_data_dir = Path(__file__).parent.parent / "tests" / "data" / "multiinstance_with_data"
    source_bpmn = test_data_dir / "multiinstance_with_data.bpmn"
    dest_dir = test_data_dir.parent / f"multiinstance_{loop_count}"
    temp_dir = tempfile.mkdtemp()

    try:
        with open(source_bpmn) as f:
            bpmn_content = f.read()

        modified_content = bpmn_content.replace("items = [item]*100", f"items = [item]*{loop_count}")

        variant_dir = Path(temp_dir) / f"multiinstance_{loop_count}"
        variant_dir.mkdir(parents=True, exist_ok=True)

        variant_bpmn = variant_dir / "multiinstance_with_data.bpmn"
        with open(variant_bpmn, "w") as f:
            f.write(modified_content)

        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        shutil.copytree(variant_dir, dest_dir)

        process_model = load_test_spec(
            process_model_id=f"test_group/multiinstance_{loop_count}",
            process_model_source_directory=f"multiinstance_{loop_count}",
        )

        user = UserService.create_user("perf_test_user", "internal", "perf_test_user")
        BpmnProcessService.persist_bpmn_process_definition(process_model.id)
        process_instance = ProcessInstanceModel(
            status="not_started",
            process_initiator=user,
            process_model_identifier=process_model.id,
            process_model_display_name=process_model.display_name,
            updated_at_in_seconds=round(time.time()),
        )
        db.session.add(process_instance)
        db.session.commit()

        ProcessInstanceQueueService.enqueue_new_process_instance(process_instance, round(time.time()))

        instrumenter.reset()

        processor = ProcessInstanceProcessor(process_instance)
        start_time = time.time()
        processor.do_engine_steps(save=False, execution_strategy_name="greedy")
        total_time = time.time() - start_time

        instrumenter.record(loop_count, total_time)

    finally:
        if Path(temp_dir).exists():
            shutil.rmtree(temp_dir)
        if dest_dir.exists():
            shutil.rmtree(dest_dir)


def clean_db():
    """Clear all tables for a fresh test run."""
    from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel

    meta = db.metadata
    db.session.execute(db.update(BpmnProcessModel).values(top_level_process_id=None))
    db.session.execute(db.update(BpmnProcessModel).values(direct_parent_process_id=None))
    for table in reversed(meta.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()


def main():
    os.environ["SPIFFWORKFLOW_BACKEND_ENV"] = "unit_testing"
    os.environ["FLASK_SESSION_SECRET_KEY"] = "e7711a3ba96c46c68e084a86952de16f"  # noqa: S105

    from spiffworkflow_backend import create_app

    connexion_app = create_app()

    with connexion_app.app.app_context():
        loop_counts = [20, 100, 200, 300]

        instrumenter = BottleneckInstrumenter()
        instrumenter.install()

        try:
            for loop_count in loop_counts:
                clean_db()
                run_single_test(instrumenter, loop_count)
        finally:
            instrumenter.uninstall()

        instrumenter.print_summary()


if __name__ == "__main__":
    main()
