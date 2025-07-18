# Use Process Metadata Backfill

This guide will show you how to use the Process Instance Metadata Backfill feature, which automatically applies new metadata extraction paths to existing process instances when they are added to a process model.

## Overview

When you add new metadata extraction paths to a process model, you typically want this metadata to be available for all process instances, including those that were created before the metadata paths were added. The Process Instance Metadata Backfill feature automatically handles this for you by:

1. Detecting when new metadata extraction paths are added to a process model
2. Automatically processing all existing process instances to extract the new metadata
3. Storing the extracted metadata for each process instance

This ensures consistent metadata reporting across all instances of a process model, regardless of when the metadata fields were added.

## Requirements

To use this feature, you must:

1. Enable Celery for background processing
2. Enable the metadata backfill feature in your configuration

## Configuration

### Environment Variables

Set the following environment variables in your deployment:

```bash
# Required: Enable Celery for background processing
SPIFFWORKFLOW_BACKEND_CELERY_ENABLED=true

# Enable the metadata backfill feature
SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_METADATA_BACKFILL_ENABLED=true
```

For complete Celery configuration including setting up Redis as a broker and backend, see [Work with Redis Celery Broker](deployment/work_with_redis_celery_broker.md). You'll need to configure settings such as:

```bash
SPIFFWORKFLOW_BACKEND_CELERY_BROKER_URL=redis://localhost
SPIFFWORKFLOW_BACKEND_CELERY_RESULT_BACKEND=redis://localhost
```

### Validation

The application will validate these settings during startup. If `SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_METADATA_BACKFILL_ENABLED` is set to `true` but Celery is not enabled, the application will fail to start.

## How It Works

### 1. Adding New Metadata Extraction Paths

When you update a process model to add new metadata extraction paths:

```json
// Before update
{
  "metadata_extraction_paths": [
    {"key": "customer_id", "path": "customer.id"}
  ]
}

// After update
{
  "metadata_extraction_paths": [
    {"key": "customer_id", "path": "customer.id"},
    {"key": "invoice_number", "path": "invoice.number"}  // New metadata path
  ]
}
```

### 2. Automatic Detection

The system automatically detects the new metadata path (`invoice_number`) when the process model is updated.

### 3. Background Processing

A Celery task is automatically triggered to backfill the new metadata:

1. The system queries all existing process instances for the process model
2. For each instance, it:
   - Retrieves the most recent completed task data
   - Extracts values for the new metadata paths from the task data
   - Adds the new metadata to the process instance

### 4. Monitoring

The backfill operation logs:
- Start and completion of the backfill process
- Number of process instances processed and updated
- Processing time
- Any errors encountered

## Performance Considerations

- The backfill process runs as a background task and won't affect application performance
- Process instances are processed in batches (default: 100 instances per batch)
- Database transactions are committed after each batch to avoid large transaction sizes

## Best Practices

1. **Monitoring**: Monitor the logs when adding new metadata fields to process models with many instances.

2. **Timing**: Consider adding new metadata fields during off-peak hours for large process models.

3. **Verification**: After backfill completes, verify that the metadata is correctly populated using process instance reports.


## FAQ

**Q: What happens if the data doesn't exist in some process instances?**  
A: The backfill process will set the metadata value to `null` for instances where the data doesn't exist.

**Q: Can I trigger a backfill manually for existing metadata paths?**  
A: The current implementation only triggers backfills when new metadata paths are added. For manual backfills, you would need to remove and re-add the metadata paths.

**Q: How long does the backfill process take?**  
A: It depends on the number of process instances and the complexity of the data. For most cases, it completes within seconds or minutes.