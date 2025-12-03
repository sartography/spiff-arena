# Reproduction Strategy for Orphaned Child Task References

## Scenario 1: Service Task Fails with PREDICTED Children

Create a BPMN process with:
1. A parent task (e.g., Parallel Gateway or Inclusive Gateway)
2. Multiple child branches
3. At least one service task that will fail
4. Child tasks that may be in PREDICTED state when the failure occurs

### BPMN Structure:
```
Start → Parallel Gateway (fork)
         ├─ Branch 1: Service Task (fails) → End
         └─ Branch 2: Script Task → End
```

### Test Code:
```python
def test_child_task_references_orphaned_on_service_task_failure():
    """Reproduce the issue where parent task references children that don't exist in DB."""

    # 1. Create a process with parallel gateway and failing service task
    process_model = load_test_spec(
        process_model_id="test/orphaned_children",
        bpmn_file_name="failing_service_with_parallel_gateway.bpmn",
    )

    # 2. Create and run process instance
    process_instance = create_process_instance_from_process_model(process_model)
    processor = ProcessInstanceProcessor(process_instance)

    # 3. Expect failure
    with pytest.raises(WorkflowExecutionServiceError):
        processor.do_engine_steps(save=True)

    # 4. Query database for parent task (parallel gateway)
    db.session.refresh(process_instance)
    processor_after_error = ProcessInstanceProcessor(process_instance)

    # Find the parallel gateway task
    parallel_gateway_spiff_task = processor_after_error.get_task_by_bpmn_identifier(
        "parallel_gateway",
        processor_after_error.bpmn_process_instance
    )
    parallel_gateway_task_model = TaskModel.query.filter_by(
        guid=str(parallel_gateway_spiff_task.id)
    ).first()

    # 5. Check children references
    children_guids = parallel_gateway_task_model.properties_json["children"]
    print(f"Parent task has {len(children_guids)} children references")

    # 6. Verify each child exists in database
    for child_guid in children_guids:
        child_task_model = TaskModel.query.filter_by(guid=child_guid).first()
        if child_task_model is None:
            print(f"ORPHANED REFERENCE FOUND: Child {child_guid} not in database!")
            # This is the bug!
```

## Scenario 2: Service Task Fails During Child Processing

This is more subtle - the failure happens while recursively processing children.

### Key Timing:
1. Parent task A creates children B and C
2. Child B is processed and added to `task_models` dict
3. Child C starts processing
4. Child C contains a service task that fails
5. Exception is raised before C is fully processed
6. Finally block saves:
   - Parent A with children=[B, C]
   - Child B (exists in task_models)
   - Child C may be incomplete or missing

### Test Code:
```python
def test_nested_service_task_failure_orphans_children():
    """Test that nested service task failures can orphan child references."""

    # BPMN structure:
    # Start → Call Activity (parent)
    #         └─ Subprocess contains:
    #            ├─ Script Task (works)
    #            └─ Service Task (fails)

    process_model = load_test_spec(
        process_model_id="test/nested_failure",
        bpmn_file_name="call_activity_with_failing_service.bpmn",
    )

    process_instance = create_process_instance_from_process_model(process_model)
    processor = ProcessInstanceProcessor(process_instance)

    with pytest.raises(WorkflowExecutionServiceError):
        processor.do_engine_steps(save=True)

    # Check all tasks in database
    all_tasks = TaskModel.query.filter_by(
        process_instance_id=process_instance.id
    ).all()

    # Build a map of existing task GUIDs
    existing_task_guids = {task.guid for task in all_tasks}

    # Check each task's children references
    orphaned_references = []
    for task in all_tasks:
        if "children" in task.properties_json:
            for child_guid in task.properties_json["children"]:
                if child_guid not in existing_task_guids:
                    orphaned_references.append({
                        "parent_guid": task.guid,
                        "parent_task_spec": task.task_definition.bpmn_identifier,
                        "orphaned_child_guid": child_guid,
                    })

    if orphaned_references:
        print(f"Found {len(orphaned_references)} orphaned child references:")
        for ref in orphaned_references:
            print(f"  Parent: {ref['parent_task_spec']} ({ref['parent_guid']})")
            print(f"    Missing child: {ref['orphaned_child_guid']}")

    assert len(orphaned_references) > 0, "Expected to find orphaned references"
```

## Scenario 3: PREDICTED Tasks Not Removed

The most likely scenario based on the code:

### When it happens:
1. A task creates PREDICTED children (future tasks in gateway paths)
2. The parent task is updated and added to `task_models` dict
3. `process_spiff_task_children()` is called
4. For PREDICTED children, `remove_spiff_task_from_parent()` is called
5. BUT if the parent was serialized AFTER the child was created, the serializer already included the child in the children array
6. A service task fails before the cleanup completes
7. Parent is saved with PREDICTED child references that aren't in the database

### Mock/Debug Code:
```python
def test_predicted_children_timing_issue():
    """Test that PREDICTED children can be orphaned due to timing."""

    # Instrument the code to track the issue
    from unittest.mock import patch

    saved_task_models = {}
    predicted_children_removed = []

    original_update_task_model = TaskService.update_task_model
    def tracked_update_task_model(self, task_model, spiff_task):
        result = original_update_task_model(self, task_model, spiff_task)
        # Record when task is serialized with children
        if "children" in task_model.properties_json:
            saved_task_models[task_model.guid] = list(task_model.properties_json["children"])
        return result

    original_remove_from_parent = TaskService.remove_spiff_task_from_parent
    @classmethod
    def tracked_remove_from_parent(cls, spiff_task, task_models):
        predicted_children_removed.append(str(spiff_task.id))
        return original_remove_from_parent(spiff_task, task_models)

    with patch.object(TaskService, 'update_task_model', tracked_update_task_model):
        with patch.object(TaskService, 'remove_spiff_task_from_parent', tracked_remove_from_parent):
            # Run process that will fail
            process_model = load_test_spec(...)
            process_instance = create_process_instance_from_process_model(process_model)
            processor = ProcessInstanceProcessor(process_instance)

            try:
                processor.do_engine_steps(save=True)
            except WorkflowExecutionServiceError:
                pass

    # Analyze what happened
    print(f"Tasks serialized with children: {len(saved_task_models)}")
    print(f"PREDICTED children removed: {len(predicted_children_removed)}")

    # Check for orphaned references
    for parent_guid, children_at_save_time in saved_task_models.items():
        for child_guid in children_at_save_time:
            if child_guid in predicted_children_removed:
                print(f"TIMING ISSUE: Parent {parent_guid} was serialized with child {child_guid}")
                print(f"  but child was later marked as PREDICTED and removed")
                print(f"  If failure occurred between these events, child will be orphaned")
```

## Recommended Fixes

### Option 1: Re-serialize Parent Before Saving
After processing all children, re-serialize the parent task to ensure the children array is accurate:

```python
def process_spiff_task_children(self, spiff_task: SpiffTask) -> None:
    for child_spiff_task in spiff_task.children:
        if child_spiff_task.has_state(TaskState.PREDICTED_MASK):
            self.__class__.remove_spiff_task_from_parent(child_spiff_task, self.task_models)
            continue
        self.update_task_model_with_spiff_task(spiff_task=child_spiff_task)
        self.process_spiff_task_children(spiff_task=child_spiff_task)

    # NEW: Re-serialize parent to ensure children array is accurate
    if str(spiff_task.id) in self.task_models:
        parent_task_model = self.task_models[str(spiff_task.id)]
        new_properties_json = self.serializer.to_dict(spiff_task)
        parent_task_model.properties_json = new_properties_json
```

### Option 2: Validate Before Commit
Add validation before committing to ensure all child references exist:

```python
def save_objects_to_database(self, save_process_instance_events: bool = True) -> None:
    # Validate child references
    task_guids = set(self.task_models.keys())
    for task_model in self.task_models.values():
        if "children" in task_model.properties_json:
            for child_guid in task_model.properties_json["children"]:
                if child_guid not in task_guids:
                    # Remove orphaned reference
                    new_props = copy.copy(task_model.properties_json)
                    new_props["children"].remove(child_guid)
                    task_model.properties_json = new_props

    # Continue with normal save
    db.session.bulk_save_objects(self.bpmn_processes.values())
    db.session.bulk_save_objects(self.task_models.values())
    if save_process_instance_events:
        db.session.bulk_save_objects(self.process_instance_events.values())
    JsonDataModel.insert_or_update_json_data_records(self.json_data_dicts)
```

### Option 3: Cleanup After Load
Add a database migration or startup check that validates and cleans orphaned references:

```python
def cleanup_orphaned_child_references(process_instance_id: int) -> int:
    """Remove child references that don't exist in the database."""
    tasks = TaskModel.query.filter_by(process_instance_id=process_instance_id).all()
    task_guids = {task.guid for task in tasks}

    cleaned_count = 0
    for task in tasks:
        if "children" in task.properties_json:
            children = task.properties_json["children"]
            valid_children = [c for c in children if c in task_guids]

            if len(valid_children) != len(children):
                new_props = copy.copy(task.properties_json)
                new_props["children"] = valid_children
                task.properties_json = new_props
                cleaned_count += 1

    if cleaned_count > 0:
        db.session.commit()

    return cleaned_count
```
