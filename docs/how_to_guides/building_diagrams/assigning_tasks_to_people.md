# Assigning Tasks to People

This guide explains how to assign tasks to specific users, roles, or groups in your BPMN workflows.

## Overview

In SpiffWorkflow, task assignment is primarily managed through **Lanes** within your BPMN diagrams. Lanes allow you to:

- Assign tasks to specific roles or departments
- Route work to the appropriate personnel
- Control who can execute particular tasks in a workflow

## Using Lanes for Task Assignment

Lanes are subdivisions within a Pool that assign activities to specific roles, systems, or departments. When a human task is placed within a Lane, only users associated with that Lane can complete the task.

![Lanes Example](/images/lanes_1.png)

### Basic Lane Setup

1. Create a Pool in your BPMN diagram
2. Add Lanes to represent different roles (e.g., "Requester", "Manager", "Approver")
3. Place human tasks within the appropriate Lane
4. Configure the Lane with a name and unique ID

| Field    | Description                                                 |
| -------- | ----------------------------------------------------------- |
| **Name** | A descriptive label representing the role (e.g., "Manager") |
| **ID**   | A unique identifier for the Lane (e.g., "lane_manager")     |

```{admonition} Note
Each Pool requires Lane configuration, even if it contains just a single Lane.
```

## Methods to Assign Lane Owners

There are two primary methods to specify who owns a Lane (i.e., who can complete tasks in that Lane):

### Method 1: Using User Groups

Lane owners can be specified using predefined user groups configured in the system.

User groups are typically defined in a YAML configuration file:

```yaml
groups:
  admin:
    users:
      - user1@spiffworkflow.org
      - user2@spiffworkflow.org
  reviewers:
    users:
      - user3@spiffworkflow.org
      - user4@spiffworkflow.org
```

When a Lane name matches a group name in the configuration, users in that group can complete tasks in the Lane.

For more information on configuring user groups, see the [permissions documentation](/how_to_guides/deployment/manage_permissions).
You can also configure the system to respect group membership defined through your OpenID provider; see [Configuring an OpenID Provider](/how_to_guides/deployment/configure_openid_provider).

### Method 2: Using Script Tasks

Script tasks enable dynamic assignment of lane owners within the workflow. You can specify the lane owners directly in the workflow logic.

```python
# Script task to assign lane owners
lane_owners = {
    "Reviewer": ["user1@example.com", "user2@example.com"]
}
```

The dictionary maps Lane names to lists of users who can complete tasks in that Lane.

```{admonition} Note
Specifying a user group in the `lane_owners` dictionary in a script task does not require it to previously exist in the database.
```

## Dynamic Task Assignment

### Excluding the Process Initiator from Approvers

A common requirement is ensuring that the person who started a process cannot approve their own request. Here's how to implement this:

```python
# Define the group identifier dynamically based on process data
group_identifier = "approvers"
group_members = get_group_members(group_identifier)

# Retrieve the process initiator's username
initiator = get_process_initiator_user()
initiator_username = initiator["username"]

# Exclude the initiator from the approvers' list if they are part of it
if initiator_username in group_members:
    group_members.remove(initiator_username)

# Assign the modified group list to the lane for task assignment
lane_owners = {"Approval": group_members}
```

### Getting Group Members Dynamically

You can use the `get_group_members()` function to fetch users belonging to a specific group:

```python
group_members = get_group_members("approvers")
```

This is useful for:

- Sending notifications to specific groups
- Dynamic task assignment based on workflow conditions
- Building approval workflows with multiple potential approvers

### Determining the Current Task's Lane

In pre/post scripts, you can determine which Lane the current task belongs to:

```python
# Get the lane name as a string
lane_name = task.task_spec.lane

# Use the lane name to get group members for notifications
group_members = get_group_members(lane_name)
```

## Example: Petty Cash Request Process

This example demonstrates task assignment across different Lanes for a petty cash request workflow.

![Lanes and Pools Example](/images/lanes_pools_example_1.png)

### Process Flow

1. **Start Event**: The workflow begins in the Requester Lane.

2. **User Task: Petty Cash Request** (Requester Lane): Collects the request details including amount and reason.

   ![Petty Cash Request Form](/images/lanes_pools_example_2.png)

3. **User Task: Approve Petty Cash** (Cashier Lane): The cashier reviews and approves the request.

   ![Approve Petty Cash Form](/images/lanes_pools_example_3.png)

4. **Manual Task: Display Output** (Requester Lane): Shows the approval result to the requester.

   ```markdown
   Your petty cash request for {{amount}} has been approved by {{approved_by}}
   ```

   ![Display Output](/images/lanes_pools_example_4.png)

## Integrating with External Role Management

If you manage user roles in an external system (like an OpenID provider), you can:

1. Configure your OpenID system to include group/role information in user tokens
2. Access this information in your BPMN diagrams through Lanes
3. Map external roles to Lane assignments

## Best Practices

1. **Use descriptive Lane names** that clearly indicate the role or department responsible for tasks.

2. **Keep Lane assignments simple** when possible - complex assignment logic can make workflows harder to maintain.

3. **Use script tasks for dynamic assignment** when you need to adjust task ownership based on workflow data or conditions.

4. **Test your assignments** to ensure tasks route to the correct users in all scenarios.

5. **Document your Lane structure** so team members understand who is responsible for each part of the workflow.

## Related Topics

- [Pools and Lanes Reference](/reference/bpmn/pools_and_lanes)
- [Script Tasks](/reference/bpmn/script_tasks)
- [Managing Permissions](/how_to_guides/deployment/manage_permissions)
