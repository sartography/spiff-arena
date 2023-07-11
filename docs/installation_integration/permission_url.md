# Permission URL

The permission URL, or target URI, refers to the specific endpoint or resource that is being granted permission to perform certain actions.

- **PG:** [process_group_identifier]: Applies to the specified process group, including all sub process groups and process models.
- **PM:** [process_model_identifier]: Applies to the specified process model.
- **BASIC:** Provides basic access to complete tasks and use the site.
- **ELEVATED:** Enables operations that require elevated permissions.
- **ALL:** Grants access to all API endpoints, providing admin-like permissions.

```{admonition} Note
An asterisk (*) can be used as a wildcard to give access to everything within a specific category. For example, "/process-models/", allows access to all resources related to process models. 
```

## PG

Process Groups permissions controls access rights granted to users or entities within that particular process model. By assigning permissions to process groups, you can determine what actions or operations users can perform within those groups. 

[View GIT Repository - BASIC](https://github.com/sartography/spiff-arena/blob/main/spiffworkflow-backend/src/spiffworkflow_backend/services/authorization_service.py#L557)

```python
def set_process_model_permissions(cls, target: str, permission_set: str) -> list[PermissionToAssign]:
```

## PM

These permissions relates to process models. It defines the permissions and access rights assigned to users or entities specifically within a given process model.

[View GIT Repository - BASIC](https://github.com/sartography/spiff-arena/blob/main/spiffworkflow-backend/src/spiffworkflow_backend/services/authorization_service.py#L574)

```python
def set_process_group_permissions(cls, target: str, permission_set: str) -> list[PermissionToAssign]:
```

## BASIC 

These permissions cover basic actions such as creating users and process instances, checking user existence, and reading various entities like process groups, models, and tasks.

[View GIT Repository - BASIC](https://github.com/sartography/spiff-arena/blob/main/spiffworkflow-backend/src/spiffworkflow_backend/services/authorization_service.py#L494)

```python
def set_basic_permissions(cls) -> list[PermissionToAssign]:
```

## ELEVATED 

These permissions cover basic actions such as creating users and process instances, checking user existence, and reading various entities like process groups, models, and tasks.

[View GIT Repository - BASIC](https://github.com/sartography/spiff-arena/blob/main/spiffworkflow-backend/src/spiffworkflow_backend/services/authorization_service.py#L494)

```python
def explode_permissions(cls, permission_set: str, target: str) -> list[PermissionToAssign]:
```


## ALL

The "ALL" permission grants unrestricted access to all API endpoints. It essentially provides administrator-like permissions, allowing the user to perform any action or operation available within the system.

```python
elif target == "ALL":
            for permission in permissions:
                permissions_to_assign.append(PermissionToAssign(permission=permission, target_uri="/*"))
        elif target.startswith("/"):
            for permission in permissions:
                permissions_to_assign.append(PermissionToAssign(permission=permission, target_uri=target))
```



### ALL URLs

```python
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
