"""Performance test measuring key operations in spiff-arena multiinstance execution.

Measures:
1. SpiffTask.run() - Pure SpiffWorkflow execution
2. update_bpmn_process() - BPMN process updates (includes workflow data serialization)
3. find_or_create_task_model() - Task model lookup and creation
4. Other - Unaccounted framework overhead
"""

import shutil
import tempfile
import time
from pathlib import Path

import pytest
from flask.app import Flask
from SpiffWorkflow.task import Task as SpiffTask
from starlette.testclient import TestClient

from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.task_service import TaskService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class BottleneckInstrumenter:
    """Instrument key operations in task processing."""

    def __init__(self):
        # Counters
        self.spiff_run_count = 0
        self.update_bpmn_process_count = 0
        self.find_or_create_count = 0

        # Timers
        self.spiff_run_time = 0.0
        self.update_bpmn_process_time = 0.0
        self.find_or_create_time = 0.0

        # Store originals
        self.original_spiff_run = SpiffTask.run
        self.original_update_bpmn_process = TaskService.update_bpmn_process
        self.original_find_or_create = TaskService.find_or_create_task_model_from_spiff_task

    def install(self):
        """Install instrumentation."""
        instrumenter = self

        def instrumented_spiff_run(spiff_task_self):
            start = time.time()
            result = instrumenter.original_spiff_run(spiff_task_self)
            instrumenter.spiff_run_time += time.time() - start
            instrumenter.spiff_run_count += 1
            return result

        def instrumented_update_bpmn_process(service_self, spiff_workflow, bpmn_process):
            start = time.time()
            result = instrumenter.original_update_bpmn_process(service_self, spiff_workflow, bpmn_process)
            instrumenter.update_bpmn_process_time += time.time() - start
            instrumenter.update_bpmn_process_count += 1
            return result

        def instrumented_find_or_create(service_self, spiff_task):
            start = time.time()
            result = instrumenter.original_find_or_create(service_self, spiff_task)
            instrumenter.find_or_create_time += time.time() - start
            instrumenter.find_or_create_count += 1
            return result

        SpiffTask.run = instrumented_spiff_run
        TaskService.update_bpmn_process = instrumented_update_bpmn_process
        TaskService.find_or_create_task_model_from_spiff_task = instrumented_find_or_create

    def uninstall(self):
        """Remove instrumentation."""
        SpiffTask.run = self.original_spiff_run
        TaskService.update_bpmn_process = self.original_update_bpmn_process
        TaskService.find_or_create_task_model_from_spiff_task = self.original_find_or_create

    def reset(self):
        """Reset counters."""
        self.spiff_run_count = 0
        self.update_bpmn_process_count = 0
        self.find_or_create_count = 0

        self.spiff_run_time = 0.0
        self.update_bpmn_process_time = 0.0
        self.find_or_create_time = 0.0

    def report(self, loop_count: int, total_time: float):
        """Print performance report."""
        # Store data for summary table
        if not hasattr(self.__class__, "results"):
            self.__class__.results = []

        self.__class__.results.append(
            {
                "loop_count": loop_count,
                "total_time": total_time,
                "spiff_run_time": self.spiff_run_time,
                "spiff_run_count": self.spiff_run_count,
                "update_bpmn_time": self.update_bpmn_process_time,
                "update_bpmn_count": self.update_bpmn_process_count,
                "find_create_time": self.find_or_create_time,
                "find_create_count": self.find_or_create_count,
            }
        )

        print(f"\n{loop_count} items: {total_time:.2f}s total")

    @classmethod
    def print_summary(cls):
        """Print final summary table after all tests."""
        if not hasattr(cls, "results") or not cls.results:
            return

        print("\n" + "=" * 120)
        print("PERFORMANCE SUMMARY - Time per Operation")
        print("=" * 120)

        # Header
        print(
            f"{'Items':<8} {'Total':>8}   {'SpiffTask.run()':>28}   {'update_bpmn_process()':>28}   "
            f"{'find_or_create()':>28}   {'Other':>16}"
        )
        print(
            f"{'':8} {'(sec)':>8}   {'Calls':>7} {'Time':>7} {'%':>5} {'ms':>6}   "
            f"{'Calls':>7} {'Time':>7} {'%':>5} {'ms':>6}   "
            f"{'Calls':>7} {'Time':>7} {'%':>5} {'ms':>6}   {'Time':>7} {'%':>5}"
        )
        print("-" * 120)

        # Data rows
        for r in cls.results:
            total = r["total_time"]

            spiff_ms = (r["spiff_run_time"] / r["spiff_run_count"] * 1000) if r["spiff_run_count"] > 0 else 0
            spiff_pct = (r["spiff_run_time"] / total * 100) if total > 0 else 0

            bpmn_ms = (r["update_bpmn_time"] / r["update_bpmn_count"] * 1000) if r["update_bpmn_count"] > 0 else 0
            bpmn_pct = (r["update_bpmn_time"] / total * 100) if total > 0 else 0

            find_ms = (r["find_create_time"] / r["find_create_count"] * 1000) if r["find_create_count"] > 0 else 0
            find_pct = (r["find_create_time"] / total * 100) if total > 0 else 0

            other_time = total - r["spiff_run_time"] - r["update_bpmn_time"] - r["find_create_time"]
            other_pct = (other_time / total * 100) if total > 0 else 0

            print(
                f"{r['loop_count']:<8} {total:>8.2f}   "
                f"{r['spiff_run_count']:>7} {r['spiff_run_time']:>7.2f} {spiff_pct:>5.1f} {spiff_ms:>6.2f}   "
                f"{r['update_bpmn_count']:>7} {r['update_bpmn_time']:>7.2f} {bpmn_pct:>5.1f} {bpmn_ms:>6.2f}   "
                f"{r['find_create_count']:>7} {r['find_create_time']:>7.2f} {find_pct:>5.1f} {find_ms:>6.2f}   "
                f"{other_time:>7.2f} {other_pct:>5.1f}"
            )

        print("=" * 120)

        # Scaling analysis
        if len(cls.results) >= 2:
            baseline = cls.results[0]
            print("\nScaling Analysis (vs 20 items baseline):")
            print(
                f"{'Items':<8} {'Expected':>10} {'Total':>10} {'SpiffTask':>10} {'update_bpmn':>12} "
                f"{'find_create':>12} {'Other':>10}"
            )
            print("-" * 74)

            for r in cls.results[1:]:
                expected = r["loop_count"] / baseline["loop_count"]
                total_scale = r["total_time"] / baseline["total_time"] if baseline["total_time"] > 0 else 0
                spiff_scale = r["spiff_run_time"] / baseline["spiff_run_time"] if baseline["spiff_run_time"] > 0 else 0
                bpmn_scale = r["update_bpmn_time"] / baseline["update_bpmn_time"] if baseline["update_bpmn_time"] > 0 else 0
                find_scale = r["find_create_time"] / baseline["find_create_time"] if baseline["find_create_time"] > 0 else 0

                baseline_other = (
                    baseline["total_time"]
                    - baseline["spiff_run_time"]
                    - baseline["update_bpmn_time"]
                    - baseline["find_create_time"]
                )
                current_other = r["total_time"] - r["spiff_run_time"] - r["update_bpmn_time"] - r["find_create_time"]
                other_scale = current_other / baseline_other if baseline_other > 0 else 0

                print(
                    f"{r['loop_count']:<8} {expected:>9.1f}x {total_scale:>9.1f}x {spiff_scale:>9.1f}x "
                    f"{bpmn_scale:>11.1f}x {find_scale:>11.1f}x {other_scale:>9.1f}x"
                )

        print("\n")


class TestMultiinstancePerformanceBottlenecks(BaseTest):
    """Performance test for multiinstance BPMN processes."""

    instrumenter = BottleneckInstrumenter()

    @classmethod
    def setup_class(cls):
        """Install instrumentation once."""
        cls.instrumenter.install()

    @classmethod
    def teardown_class(cls):
        """Remove instrumentation and print summary."""
        cls.instrumenter.uninstall()
        cls.instrumenter.print_summary()

    @pytest.mark.parametrize("loop_count", [20, 100, 200, 300])
    def test_bottleneck_analysis(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        loop_count: int,
    ) -> None:
        """Measure key operation performance."""
        # Create temporary directory for test variant
        temp_dir = tempfile.mkdtemp()

        try:
            # Get source BPMN and create modified copy in temp directory
            test_data_dir = Path(__file__).parent.parent.parent / "data" / "multiinstance_with_data"
            source_bpmn = test_data_dir / "multiinstance_with_data.bpmn"

            with open(source_bpmn) as f:
                bpmn_content = f.read()

            # Create modified BPMN with specified loop count
            modified_content = bpmn_content.replace("items = [item]*100", f"items = [item]*{loop_count}")

            # Create temp test directory structure
            variant_dir = Path(temp_dir) / f"multiinstance_{loop_count}"
            variant_dir.mkdir(parents=True, exist_ok=True)

            variant_bpmn = variant_dir / "multiinstance_with_data.bpmn"
            with open(variant_bpmn, "w") as f:
                f.write(modified_content)

            # Copy to test data location (cleaned up by with_db_and_bpmn_file_cleanup)
            dest_dir = test_data_dir.parent / f"multiinstance_{loop_count}"
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            shutil.copytree(variant_dir, dest_dir)

            # Load process
            process_model = load_test_spec(
                process_model_id=f"test_group/multiinstance_{loop_count}",
                process_model_source_directory=f"multiinstance_{loop_count}",
            )

            # Create process instance
            process_instance = self.create_process_instance_from_process_model(
                process_model=process_model, save_start_and_end_times=False
            )

            # Reset counters
            self.instrumenter.reset()

            # Measure execution
            processor = ProcessInstanceProcessor(process_instance)

            start_time = time.time()
            processor.do_engine_steps(save=False, execution_strategy_name="greedy")
            total_time = time.time() - start_time

            # Generate report
            self.instrumenter.report(loop_count, total_time)

        finally:
            # Cleanup temporary directory
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)
