allow filtering process instances by last milestone. i tried just hacking a post (that fetches process instances like this, but of course our code doesn't support it):

```json
{
  "report_metadata": {
    "columns": [
      {
        "Header": "Id",
        "accessor": "id",
        "filterable": false,
        "filter_field_value": "",
        "filter_operator": ""
      },
      {
        "Header": "Process",
        "accessor": "process_model_display_name",
        "filterable": false,
        "filter_field_value": "",
        "filter_operator": ""
      },
      {
        "Header": "Start",
        "accessor": "start_in_seconds",
        "filterable": false,
        "filter_field_value": "",
        "filter_operator": ""
      },
      {
        "Header": "End",
        "accessor": "end_in_seconds",
        "filterable": false,
        "filter_field_value": "",
        "filter_operator": ""
      },
      {
        "Header": "Started by",
        "accessor": "process_initiator_username",
        "filterable": false,
        "filter_field_value": "",
        "filter_operator": ""
      },
      {
        "Header": "Last milestone",
        "accessor": "last_milestone_bpmn_name",
        "filterable": false,
        "filter_field_value": "",
        "filter_operator": ""
      },
      {
        "Header": "Status",
        "accessor": "status",
        "filterable": false,
        "filter_field_value": "",
        "filter_operator": ""
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

the UX on the frontend also needs to support it.
we should have a test in spiffworkflow-frontend/test/browser that proves that it works.
those get run like cd spiffworkflow-frontend && HEADLESS=true pytest spiffworkflow-frontend/test/browser/test_login.py (you will make a new file)
always run ./bin/run_pyl from the root of the repo as you make changes to make sure unit tests and lint are staying in a working state.
feel free to flesh out this spec, add detail, add TODO items, etc.
