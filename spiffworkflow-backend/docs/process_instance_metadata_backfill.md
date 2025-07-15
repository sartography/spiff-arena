# Process Instance Metadata Backfill Specification

## Overview

This specification describes a new feature that enables automatic backfilling of process instance metadata when new metadata fields are added to a process model. When enabled, any new process instance metadata added to a process model will be applied retroactively to all existing process instances as if the metadata had been added at the beginning.

## Requirements

1. The feature shall be opt-in via an environment variable configuration option.
2. The feature shall only be available when Celery is enabled.
3. The application shall fail fast if the feature is enabled but Celery is not enabled.
4. When enabled, any new process instance metadata added to a process model shall be backfilled to all existing process instances of that model.

## Configuration

### Environment Variable

```
SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_METADATA_BACKFILL_ENABLED=true
```

Default value: `false`

### Validation

- During application startup, if `SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_METADATA_BACKFILL_ENABLED` is set to `true`, the application will check if Celery is enabled.
- If Celery is not enabled, the application will fail to start with an appropriate error message.

## Implementation Details

### Metadata Change Detection

1. When a process model is updated, the system will compare the new metadata configuration with the previous version.
2. If new metadata fields are detected, and the backfill feature is enabled, a backfill task will be scheduled.

### Backfill Process

1. A Celery task will be created to handle the backfill process.
2. The task will:
   - Query all existing process instances for the given process model
   - For each process instance, apply the new metadata fields
   - Update the process instance records in the database

### Performance Considerations

1. The backfill will be performed as a background task to avoid impacting application performance.
2. For process models with many instances, the backfill task will process instances in batches to manage memory usage.
3. The backfill task should be idempotent to handle potential failures and retries.

### Logging and Monitoring

1. The start and completion of the backfill process will be logged.
2. Metrics will be recorded for:
   - Number of process instances updated
   - Processing time
   - Any errors encountered

## Error Handling

1. If the backfill process fails, it should be retried with appropriate backoff strategies.
2. Failures should be logged with sufficient detail to diagnose the issue.
3. The backfill process should not interfere with normal application operation.

## Security Considerations

1. The backfill process will maintain the existing access control and data privacy constraints.
2. No additional permissions will be granted to the backfill process beyond what is required to update the process instances.

## Testing Requirements

1. Unit tests to verify the detection of metadata changes.
2. Integration tests to verify the backfill process correctly updates existing process instances.
3. Tests for the application startup validation when the feature is enabled without Celery.

## Implementation Todo List

### Configuration Setup

- [ ] Add `SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_METADATA_BACKFILL_ENABLED` environment variable to `default.py` with a default value of `False`
- [ ] Add validation in `config/__init__.py` to check if Celery is enabled when metadata backfill is enabled
- [ ] Update configuration documentation to include the new environment variable

### Metadata Change Detection

- [ ] Create a service to detect changes in process model metadata:
  - [ ] Add a function to compare previous and new metadata extraction paths in ProcessModelInfo
  - [ ] Identify new metadata fields that have been added
  - [ ] Skip if no new metadata fields are detected

### Celery Task Implementation

- [ ] Create a new Celery task in `src/spiffworkflow_backend/background_processing/celery_tasks/metadata_backfill_task.py`:
  - [ ] Implement task function to accept process model identifier and new metadata fields
  - [ ] Add logging for task start and completion
  - [ ] Add error handling with appropriate exception classes
  - [ ] Implement retry logic with backoff for failed tasks

### Metadata Extraction and Backfill

- [ ] Create a metadata backfill service in `src/spiffworkflow_backend/services/metadata_backfill_service.py`:
  - [ ] Implement batch processing for large numbers of process instances
  - [ ] Implement extraction of metadata values from existing process instances
  - [ ] Create method to apply new metadata fields to process instances, finding the most recent task for each instance, finding that tasks's data, and using that data as the source for the metadata value (if the data exists within the task)
  - [ ] Implement database transaction handling to ensure atomic updates

### Integration with Process Model Update Flow

- [ ] Modify process model update logic to trigger metadata backfill when changes are detected:
  - [ ] Add hook in process model update flow to check for metadata changes
  - [ ] Schedule the backfill Celery task if changes are detected and feature is enabled
  - [ ] Add logging for scheduled backfill tasks

### Database Updates

- [ ] Ensure `ProcessInstanceMetadataModel` table can handle the additional records efficiently:
  - [ ] Review and optimize indexes if necessary
  - [ ] Consider database performance implications for large-scale backfills

### Testing

- [ ] Create unit tests for metadata change detection
- [ ] Create integration tests for the complete backfill flow
- [ ] Add tests for configuration validation

### Documentation

- [ ] Update API documentation to include information about the backfill feature (this goes in ../docs, where .. is the root of the git repo, and ../docs is where we put all docs)
- [ ] Document the environment variable in the configuration guide
- [ ] Add examples of usage and expected behavior

### Monitoring and Diagnostics

- [ ] Add metrics collection for backfill operations:
  - [ ] Track number of instances updated per backfill task
  - [ ] Track processing time for backfill operations
  - [ ] Log errors and exceptions with detailed context

### Deployment and Release

- [ ] Create database migration script if needed
- [ ] Create deployment documentation with configuration examples

