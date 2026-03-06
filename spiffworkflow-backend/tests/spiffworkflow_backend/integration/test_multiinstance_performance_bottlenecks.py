"""Performance test measuring key operations in spiff-arena multiinstance execution.

Measures the actual bottlenecks:
1. serializer.to_dict() - Full workflow serialization
2. update_task_model_with_spiff_task() - Per-task model update (the main bottleneck)
3. flush_dirty_bpmn_process_updates() - Deferred BPMN process updates
4. save_objects_to_database() - DB bulk persistence
"""
import shutil
import tempfile
import time
from functools import wraps
from pathlib import Path

import pytest
from flask.app import Flask
from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.task import Task as SpiffTask
from starlette.testclient import TestClient

from spiffworkflow_backend.services.task_service import TaskService
from spiffworkflow_backend.services.workflow_execution_service import ExecutionStrategy
from spiffworkflow_backend.services.workflow_execution_service import TaskModelSavingDelegate
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class MethodTimer:
    """Track call count and cumulative time for a method."""

    def __init__(self, name: str):
        self.name = name
        self.count = 0
        self.total_time = 0.0

    def reset(self):
        self.count = 0
        self.total_time = 0.0


class BottleneckInstrumenter:
    """Instrument key operations in task processing."""

    def __init__(self):
        self.timers: dict[str, MethodTimer] = {}
        self._patches: list[tuple] = []

    def _create_timer(self, name: str) -> MethodTimer:
        timer = MethodTimer(name)
        self.timers[name] = timer
        return timer

    def _patch_instance_method(self, cls, method_name: str, timer: MethodTimer):
        original = getattr(cls, method_name)
        self._patches.append((cls, method_name, original))

        @wraps(original)
        def wrapper(self_arg, *args, **kwargs):
            start = time.perf_counter()
            result = original(self_arg, *args, **kwargs)
            timer.total_time += time.perf_counter() - start
            timer.count += 1
            return result

        setattr(cls, method_name, wrapper)

    def install(self):
        """Install instrumentation on key methods."""
        # spiff_run loop internals
        self._patch_instance_method(
            SpiffTask, "run",
            self._create_timer("SpiffTask.run"),
        )
        self._patch_instance_method(
            BpmnWorkflow, "refresh_waiting_tasks",
            self._create_timer("refresh_waiting"),
        )
        self._patch_instance_method(
            ExecutionStrategy, "get_ready_engine_steps",
            self._create_timer("get_ready_steps"),
        )
        self._patch_instance_method(
            TaskModelSavingDelegate, "did_complete_task",
            self._create_timer("did_complete_task"),
        )
        # after_engine_steps internals
        self._patch_instance_method(
            BpmnWorkflowSerializer, "to_dict",
            self._create_timer("serializer.to_dict"),
        )
        self._patch_instance_method(
            TaskService, "update_task_model_with_spiff_task",
            self._create_timer("update_task_model"),
        )
        self._patch_instance_method(
            TaskService, "flush_dirty_bpmn_process_updates",
            self._create_timer("flush_dirty_bpmn"),
        )
        self._patch_instance_method(
            TaskService, "save_objects_to_database",
            self._create_timer("save_to_db"),
        )

    def uninstall(self):
        for cls, method_name, original in self._patches:
            setattr(cls, method_name, original)
        self._patches.clear()

    def reset(self):
        for timer in self.timers.values():
            timer.reset()

    def report(self, loop_count: int, total_time: float):
        if not hasattr(self.__class__, "results"):
            self.__class__.results = []

        result = {"loop_count": loop_count, "total_time": total_time}
        for name, timer in self.timers.items():
            result[f"{name}_time"] = timer.total_time
            result[f"{name}_count"] = timer.count
        self.__class__.results.append(result)

        print(f"\n{loop_count} items: {total_time:.3f}s total")

    @classmethod
    def print_summary(cls):
        if not hasattr(cls, "results") or not cls.results:
            return

        timer_names = []
        for key in cls.results[0]:
            if key.endswith("_time") and key != "total_time":
                timer_names.append(key.removesuffix("_time"))

        col_w = max(len(n) for n in timer_names)
        col_w = max(col_w, 10)

        print("\n" + "=" * 140)
        print("PERFORMANCE SUMMARY")
        print("=" * 140)

        header = f"{'Items':<8} {'Total':>8} |"
        for name in timer_names:
            header += f" {name:>{col_w}} {'calls':>6} {'%':>5} {'ms/call':>7} |"
        header += f" {'Other':>8} {'%':>5}"
        print(header)
        print("-" * 140)

        for r in cls.results:
            total = r["total_time"]
            tracked = sum(r[f"{n}_time"] for n in timer_names)
            other = total - tracked
            other_pct = (other / total * 100) if total > 0 else 0

            row = f"{r['loop_count']:<8} {total:>8.3f} |"
            for name in timer_names:
                t = r[f"{name}_time"]
                c = r[f"{name}_count"]
                pct = (t / total * 100) if total > 0 else 0
                ms = (t / c * 1000) if c > 0 else 0
                row += f" {t:>{col_w}.3f} {c:>6} {pct:>5.1f} {ms:>7.2f} |"
            row += f" {other:>8.3f} {other_pct:>5.1f}"
            print(row)

        print("=" * 140)

        if len(cls.results) >= 2:
            baseline = cls.results[0]
            print(f"\nScaling Analysis (vs {baseline['loop_count']} items baseline):")

            scale_header = f"{'Items':<8} {'Expected':>10} {'Total':>10} |"
            for name in timer_names:
                scale_header += f" {name:>{col_w}} |"
            scale_header += f" {'Other':>10}"
            print(scale_header)
            print("-" * 140)

            baseline_tracked = sum(baseline[f"{n}_time"] for n in timer_names)
            baseline_other = baseline["total_time"] - baseline_tracked

            for r in cls.results[1:]:
                expected = r["loop_count"] / baseline["loop_count"]
                total_scale = r["total_time"] / baseline["total_time"] if baseline["total_time"] > 0 else 0

                row = f"{r['loop_count']:<8} {expected:>9.1f}x {total_scale:>9.1f}x |"
                for name in timer_names:
                    bt = baseline[f"{name}_time"]
                    ct = r[f"{name}_time"]
                    scale = ct / bt if bt > 0 else 0
                    row += f" {scale:>{col_w}.1f}x |"

                current_tracked = sum(r[f"{n}_time"] for n in timer_names)
                current_other = r["total_time"] - current_tracked
                other_scale = current_other / baseline_other if baseline_other > 0 else 0
                row += f" {other_scale:>9.1f}x"
                print(row)

        print()


class TestMultiinstancePerformanceBottlenecks(BaseTest):
    """Performance test for multiinstance BPMN processes."""

    instrumenter = BottleneckInstrumenter()

    @classmethod
    def setup_class(cls):
        cls.instrumenter.install()

    @classmethod
    def teardown_class(cls):
        cls.instrumenter.uninstall()
        cls.instrumenter.print_summary()

    @pytest.mark.parametrize("loop_count", [20,200])
    def test_bottleneck_analysis(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        loop_count: int,
    ) -> None:
        """Measure key operation performance."""
        temp_dir = tempfile.mkdtemp()

        try:
            test_data_dir = Path(__file__).parent.parent.parent / "data" / "multiinstance_with_data"
            source_bpmn = test_data_dir / "multiinstance_with_data.bpmn"

            with open(source_bpmn) as f:
                bpmn_content = f.read()

            modified_content = bpmn_content.replace("items = [item]*100", f"items = [item]*{loop_count}")

            variant_dir = Path(temp_dir) / f"multiinstance_{loop_count}"
            variant_dir.mkdir(parents=True, exist_ok=True)

            variant_bpmn = variant_dir / "multiinstance_with_data.bpmn"
            with open(variant_bpmn, "w") as f:
                f.write(modified_content)

            dest_dir = test_data_dir.parent / f"multiinstance_{loop_count}"
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            shutil.copytree(variant_dir, dest_dir)

            process_model = load_test_spec(
                process_model_id=f"test_group/multiinstance_{loop_count}",
                process_model_source_directory=f"multiinstance_{loop_count}",
            )

            process_instance = self.create_process_instance_from_process_model(
                process_model=process_model, save_start_and_end_times=False
            )

            self.instrumenter.reset()

            from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor

            t0 = time.perf_counter()
            processor = ProcessInstanceProcessor(process_instance)
            processor_init_time = time.perf_counter() - t0

            start_time = time.perf_counter()
            processor.do_engine_steps(save=False, execution_strategy_name="greedy")
            total_time = time.perf_counter() - start_time

            self.instrumenter.report(loop_count, total_time)

            # Print update_task_model breakdown
            ts = processor.execution_strategy_delegate.task_service
            print(f"\n  update_task_model_with_spiff_task breakdown:")
            print(f"    find_or_create:       {ts._perf_find_or_create:.3f}s")
            print(f"    update_task_model():  {ts._perf_update_task_model_inner:.3f}s")
            print(f"      props_json lookup:  {ts._perf_props_json:.3f}s")
            print(f"      convert(task.data): {ts._perf_convert_data:.3f}s")
            print(f"      python_env:         {ts._perf_python_env:.3f}s")
            print(f"      json hash/update:   {ts._perf_json_hash:.3f}s")
            print(f"    events:               {ts._perf_events:.3f}s")
            print(f"    mark_dirty:           {ts._perf_mark_dirty:.3f}s")
            wrapper_total = (ts._perf_find_or_create + ts._perf_update_task_model_inner
                             + ts._perf_events + ts._perf_mark_dirty)
            print(f"    wrapper accounted:    {wrapper_total:.3f}s")
            print(f"\n  ProcessInstanceProcessor.__init__: {processor_init_time:.3f}s")

        finally:
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)
