# Lane Owners Implementation Plan

## Background

The goal is to support dynamic task assignment where:
1. Tasks can be assigned to groups (not just individual users)
2. Users who haven't signed in yet can be assigned to tasks (resolved when they sign in)
3. The `lane_owners` task data can specify groups using a `group:` prefix

### Example Syntax
```python
lane_owners = {
    "Reviewer": ["group:reviewers", "user1@example.com", "nonexistent@example.com"]
}
```

## Current State

### Database Models Created
- **HumanTaskGroupModel** (`human_task_group.py`): Junction table linking `human_task` to `group` for many-to-many relationship
- **HumanTaskUserWaitingModel** (`human_task_user_waiting.py`): Stores pending assignments for users who haven't signed in yet

### Interface Changes
- **PotentialOwnerIdList** updated in `interfaces.py`:
  - `lane_assignment_id`: Now `NotRequired` and deprecated (kept for backward compatibility)
  - `lane_owner_group_ids`: New required field - list of group IDs for task assignment
  - `lane_owner_usernames_waiting`: Optional list of usernames/emails for users not yet signed in

### Files Modified
- `load_database_models.py`: Added imports for new models
- `user_service.py`: Added `apply_waiting_human_task_assignments()` method to resolve pending assignments when user signs in

## Migration Strategy

### Phase 1 (Current Change)
1. **Keep `lane_assignment_id` column** on `HumanTaskModel` - don't remove it
2. **Add `HumanTaskGroupModel`** junction table
3. For **new tasks**:
   - Populate `HumanTaskGroupModel` with all relevant groups
   - Also set `lane_assignment_id` to the first group (for backward compat)
4. **Update queries** to check BOTH `HumanTaskGroupModel` OR `lane_assignment_id` (so old tasks still work)

### Phase 2 (Future PR)
1. Data migration: backfill `HumanTaskGroupModel` from existing `lane_assignment_id` values
2. Update queries to only use `HumanTaskGroupModel`
3. Eventually deprecate/remove `lane_assignment_id`

## Remaining TODO Items

### High Priority
- [ ] Update `get_potential_owners_from_task` in `process_instance_processor.py`:
  - Parse `group:` prefix in lane_owners entries
  - If lane_owners specified with groups: use those groups only (not lane name group)
  - If no lane_owners: use lane name group as single entry in `lane_owner_group_ids`
  - Collect usernames that don't exist into `lane_owner_usernames_waiting`

- [ ] Update `save()` method in `process_instance_processor.py`:
  - Create `HumanTaskGroupModel` entries for each group in `lane_owner_group_ids`
  - Create `HumanTaskUserWaitingModel` entries for usernames in `lane_owner_usernames_waiting`
  - Continue setting `lane_assignment_id` for backward compatibility

- [ ] Search for all instances of `lane_assignment_id` and update queries:
  - `update_human_task_assignments_for_user` in `user_service.py`
  - Any task list queries that filter by group membership
  - Task completion authorization checks

### Medium Priority
- [ ] Update task completion logic to check:
  - Direct user assignment (`HumanTaskUserModel`)
  - Group membership via `HumanTaskGroupModel`
  - Legacy `lane_assignment_id` for old tasks

- [ ] Add cleanup when human task completes:
  - Delete related `HumanTaskGroupModel` entries
  - Delete related `HumanTaskUserWaitingModel` entries

### Testing
- [ ] Unit tests for dynamic group assignment
- [ ] Unit tests for user-not-signed-in flow
- [ ] Integration tests for backward compatibility with existing tasks

## Key Design Decisions

1. **Groups in lane_owners override lane name**: When `lane_owners` specifies groups, we don't automatically include the lane name group. The user is explicitly defining which groups should have access.

2. **Backward compatibility**: Keep `lane_assignment_id` populated for existing queries to continue working. New code should prefer `HumanTaskGroupModel`.

3. **Waiting assignments resolved at sign-in**: `HumanTaskUserWaitingModel` entries are checked when a user signs in via `apply_waiting_human_task_assignments()`.

## Files to Modify

1. `spiffworkflow-backend/src/spiffworkflow_backend/services/process_instance_processor.py`
   - `get_potential_owners_from_task()` - parse group: prefix, populate new fields
   - `save()` - create HumanTaskGroupModel and HumanTaskUserWaitingModel entries

2. `spiffworkflow-backend/src/spiffworkflow_backend/services/user_service.py`
   - `update_human_task_assignments_for_user()` - update to use HumanTaskGroupModel

3. `spiffworkflow-backend/src/spiffworkflow_backend/routes/tasks_controller.py`
   - Task authorization checks

4. `spiffworkflow-backend/src/spiffworkflow_backend/models/human_task.py`
   - `update_attributes_from_spiff_task()` - may need updates for new fields