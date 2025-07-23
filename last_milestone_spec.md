# Last Milestone Filter Specification

## Overview
This feature allows filtering process instances by their last milestone. This is useful for users who want to quickly find process instances that have reached a specific stage or milestone in their execution.

## Backend Implementation
The backend implementation adds support for filtering process instances by the `last_milestone_bpmn_name` field. This field is already part of the `ProcessInstanceModel` in the database.

### Key Components:
- **ProcessInstanceReportService**: Updated to support filtering by last milestone name
- **FilterValue interface**: Supports the `last_milestone_bpmn_name` field in the filter configuration
- **Unit Tests**: Added tests to verify the backend filtering works correctly

### Example API Request:
```json
{
  "report_metadata": {
    "columns": [
      {
        "Header": "Id",
        "accessor": "id",
        "filterable": false
      },
      {
        "Header": "Process",
        "accessor": "process_model_display_name",
        "filterable": false
      },
      {
        "Header": "Start",
        "accessor": "start_in_seconds",
        "filterable": false
      },
      {
        "Header": "End",
        "accessor": "end_in_seconds",
        "filterable": false
      },
      {
        "Header": "Started by",
        "accessor": "process_initiator_username",
        "filterable": false
      },
      {
        "Header": "Last milestone",
        "accessor": "last_milestone_bpmn_name",
        "filterable": false
      },
      {
        "Header": "Status",
        "accessor": "status",
        "filterable": false
      }
    ],
    "filter_by": [
      {
        "field_name": "with_oldest_open_task",
        "field_value": true
      },
      {
        "field_name": "with_relation_to_me",
        "field_value": true
      },
      {
        "field_name": "last_milestone_bpmn_name",
        "field_value": "Completed",
        "operator": "equals"
      },
      {
        "field_name": "process_model_identifier",
        "field_value": "examples/agent-with-ai-connector",
        "operator": "equals"
      }
    ],
    "order_by": []
  }
}
```

## Frontend Implementation
The frontend implementation adds a dropdown in the advanced filter options to select a last milestone value for filtering process instances.

### Key Components:
- **ProcessInstanceListTableWithFilters**: Updated to include a last milestone dropdown in the advanced filters modal
- **State Management**: Added state variables for selected milestone and available milestone values
- **Data Fetching**: Added code to fetch unique milestone values from existing process instances
- **UI Components**: Added a dropdown to select milestone values in the advanced options modal

### How it Works:
1. When loading the process instances page, the system fetches unique milestone values from existing process instances
2. Users can access the last milestone filter in the advanced options modal
3. When a milestone is selected, the filter is applied and process instances are filtered to show only those with the matching last milestone value
4. The selected filter appears as a tag in the UI

## Testing
A browser test has been created to verify the last milestone filtering functionality:

- File: `spiffworkflow-frontend/test/browser/test_last_milestone_filter.py`
- The test verifies that:
  - The last milestone dropdown appears in the advanced options modal
  - A milestone can be selected from the dropdown
  - The filter is applied correctly to display only matching process instances

## Running Tests
Tests can be run with:
```bash
cd spiffworkflow-frontend && HEADLESS=true pytest spiffworkflow-frontend/test/browser/test_last_milestone_filter.py
```

Always run `./bin/run_pyl` from the root of the repo to make sure unit tests and lint are staying in a working state.
