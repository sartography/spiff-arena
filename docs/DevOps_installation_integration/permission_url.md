# Permission URL

The permission URL, or target URI, refers to the specific endpoint or resource to which permission is granted to perform certain actions.

- **PG:** [process_group_identifier]: Applies to the specified process group, including all subprocess groups and process models.
- **PM:** [process_model_identifier]: Applies to the specified process model.
- **BASIC:** Allows basic access to complete tasks and use the site.
- **SUPPORT:** BASIC permissions plus significant administrative permissions.
- **ELEVATED:** Includes SUPPORT permissions and adds the ability to view and modify secrets.
Does not include the ability to view or modify process groups and process models.
- **ALL:** Grants access to all API endpoints, without any limitations.

```{admonition} Note
An asterisk (*) can be used as a wildcard to give access to everything within a specific category.
For example, `/process-models/*` allows access to all resources related to process models.
```

This functionality is implemented in [authorization_service.py](https://github.com/sartography/spiff-arena/blob/main/spiffworkflow-backend/src/spiffworkflow_backend/services/authorization_service.py).

(pg)=
## PG

Process Group permissions control the access rights granted to users or entities within the given process group.

(pm)=
## PM

These permissions relate to process models and assign permissions and access rights to users or entities specifically within a given process model.

## BASIC

These permissions cover basic actions such as signing in to the site and completing tasks that are assigned to you.

## SUPPORT

These permissions are significant, allowing support personnel to debug process instances and take corrective action when errors occur.
In typical scenarios, a user with SUPPORT permissions would also be assigned access to view or modify process groups and models.
See [PG](#pg) and [PM](#pm).

## ELEVATED

A user with elevated permissions can do anything on the site except interact with process models.
In typical scenarios, a user with ELEVATED permissions would also be assigned access to view or modify process groups and models.

## ALL

The "ALL" permission grants unrestricted access to all API endpoints.
It provides administrator-level permissions, allowing the user to perform any action or operation available within the system.

### ALL URLs

% use bash syntax here to avoid syntax highlighting. otherwise, it gets highlighted as if it's python
```bash
  /active-users/unregister/{last_visited_identifier}:
  /active-users/updates/{last_visited_identifier}:
  /authentication_callback/{service}/{auth_method}:
  /authentications:
  /connector-proxy/typeahead/{category}:
  /debug/test-raise-error:
  /debug/version-info:
  /event-error-details/{modified_process_model_identifier}/{process_instance_id}/{process_instance_event_id}:
  /github-webhook-receive:
  /login:
  /login_api:
  /login_api_return:
  /login_return:
  /login_with_access_token:
  /logout:
  /logout_return:
  /logs/typeahead-filter-values/{modified_process_model_identifier}/{process_instance_id}:
  /logs/{modified_process_model_identifier}/{process_instance_id}:
  /messages/{message_name}:
  /messages:
  /permissions-check:
  /process-data-file-download/{modified_process_model_identifier}/{process_instance_id}/{process_data_identifier}:
  /process-data/{modified_process_model_identifier}/{process_instance_id}/{process_data_identifier}:
  /process-groups/{modified_process_group_identifier}/move:
  /process-groups/{modified_process_group_id}:
  /process-groups:
  /process-instance-reset/{modified_process_model_identifier}/{process_instance_id}/{to_task_guid}:
  /process-instance-resume/{modified_process_model_identifier}/{process_instance_id}:
  /process-instance-suspend/{modified_process_model_identifier}/{process_instance_id}:
  /process-instance-terminate/{modified_process_model_identifier}/{process_instance_id}:
  /process-instances/find-by-id/{process_instance_id}:
  /process-instances/for-me/{modified_process_model_identifier}/{process_instance_id}/task-info:
  /process-instances/for-me/{modified_process_model_identifier}/{process_instance_id}:
  /process-instances/for-me:
  /process-instances/report-metadata:
  /process-instances/reports/columns:
  /process-instances/reports/{report_id}:
  /process-instances/reports:
  /process-instances/{modified_process_model_identifier}/{process_instance_id}/run:
  /process-instances/{modified_process_model_identifier}/{process_instance_id}/task-info:
  /process-instances/{modified_process_model_identifier}/{process_instance_id}:
  /process-instances/{modified_process_model_identifier}:
  /process-instances:
  /process-model-natural-language/{modified_process_group_id}:
  /process-model-publish/{modified_process_model_identifier}:
  /process-model-tests/{modified_process_model_identifier}:
  /process-models/{modified_process_group_id}:
  /process-models/{modified_process_model_identifier}/files/{file_name}:
  /process-models/{modified_process_model_identifier}/files:
  /process-models/{modified_process_model_identifier}/move:
  /process-models/{modified_process_model_identifier}/script-unit-tests/run:
  /process-models/{modified_process_model_identifier}/script-unit-tests:
  /process-models/{modified_process_model_identifier}:
  /process-models:
  /processes/callers/{bpmn_process_identifiers}:
  /processes:
  /secrets/{key}:
  /secrets:
  /send-event/{modified_process_model_identifier}/{process_instance_id}:
  /service-tasks:
  /status:
  /task-complete/{modified_process_model_identifier}/{process_instance_id}/{task_guid}:
  /task-data/{modified_process_model_identifier}/{process_instance_id}/{task_guid}:
  /tasks/for-me:
  /tasks/for-my-groups:
  /tasks/for-my-open-processes:
  /tasks/{process_instance_id}/send-user-signal-event:
  /tasks/{process_instance_id}/{task_guid}/save-draft:
  /tasks/{process_instance_id}/{task_guid}:
  /tasks/{process_instance_id}:
  /tasks:
  /user-groups/for-current-user:
  /users/exists/by-username:
  /users/search:
```
