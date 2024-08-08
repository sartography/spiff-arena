# Pools and Lanes

A Pool represents a participant and can be seen as a self-contained process.
This participant can be an internal entity (e.g., a department within a company) or an external entity (e.g., a customer or another company).
Lanes are helpful in highlighting which specific role or department is responsible for certain activities or tasks in a process.
A process can have one or more Pools, each with one or more Lanes.

**Reasons to Use Pools and Lanes:**

- They visually represent distinct participants in a process, such as various departments, organizations, or systems.
- They help depict interactions between separate business entities, like a buyer-seller dynamic.
- They provide a clear overview of communication between different participants.
- They categorize tasks or activities based on specific roles.
- They bring structure and organization to complex diagrams that involve multiple roles, departments, or stakeholders.

## Pools

A Pool can be configured as an "Empty Pool" (collapsed) or an "Expanded Pool."
You can choose the desired configuration 🔧 from the element's options after dragging it onto your diagram.

![pools_and_lanes](images/pools_and_lanes_1.png)

Empty Pools are used to represent role players in cases where a specific process is neither known nor required, but the interaction points remain valuable.
They serve to illustrate the engagement of certain entities without detailing their internal processes.
For example, we don't know a customer's specific process, but it matters when we interact with them to complete our process.

Conversely, Expanded Pools are employed when the processes are known and hold relevance within the diagram's context.

## Lanes

Lanes group activities within a single Pool, usually signifying different roles or departments.

![lanes](images/lanes_1.png)

Lanes are incorporated into Pools when the roles they represent belong to the same entity.
However, if a process doesn't logically fit within the same Pool, like those for different organizations or businesses, it's more appropriate to represent it as a separate Pool rather than another Lane.

![lanes](images/separate_pools_1.png)

## Configuration

![participant_configuration](images/participant_configuration_1.png)

**Collapsed (Empty) Pool configuration:**

Configuring an "Empty Pool" (collapsed) to represent an external entity, such as a customer.

| 💻 Form | ⌨ Field Input | 📝 Description |
| --- | --- | --- |
| ![participant_sales](images/participant_customer_1.png) | **Participant Name:** Sales, **Participant ID:** sales, | A clear and descriptive name serves as a human-readable label or title for the participant. Additionally, a unique ID is essential to distinguish the participant from other participants. |
| ![data_object_pools](images/data_object_pools_1.png) | **Data Objects:** order_details | Create or reference a Data Object to store information for sharing between entities. |

**Expanded Pool configuration:**

Setting up an "Expanded Pool" requires referencing the process, in contrast to the setup of an empty pool.

| 💻 Form | ⌨ Field Input | 📝 Description |
| --- | --- | --- |
| ![participant_sales](images/participant_sales_1.png) | **Participant Name:** Sales, **Participant ID:** sales,  **Process ID:** process_order, **Process Name:** Process Order | A clear and descriptive name serves as a human-readable label or title for both the participant and the process. Additionally, a unique ID is essential to distinguish both the participant and the process from others. |
| ![data_object_pools](images/data_object_pools_1.png) | **Data Objects:** order_details | Create or reference a Data Object to store information for sharing between entities. |

**Collapsed Pool configuration:**

![lanes](images/lane_configuration_1.png)

Remember that each pool requires Lane configuration, even if it contains just a single Lane.
![lanes](images/pool_settings_1.png)

| 💻 Form | ⌨ Field Input | 📝 Description |
| --- | --- | --- |
| ![participant_sales](images/participant_lane_1.png) | **Name:** Manager | A concise and descriptive label that accurately represents the owner and role of the Lane. |
| ![data_object_pools](images/data_object_pools_1.png) | **ID:** lane_manager | A distinct ID to differentiate each Lane, especially when there are multiple. |

---
### Example: Using Lanes and Pools for Petty Cash Request Process

This example demonstrates the application of Lanes and Pools in a BPMN diagram, specifically designed to handle a petty cash request process within an organization.

The process is structured around different tasks allocated to Lanes and Pools, emphasizing role-based access and task execution.

#### BPMN Diagram

![Lanes and Pools Example](images/lanes_pools_example_1.png)

**Process Flow:**

1. **Start Event**: The workflow kicks off with a start event signaling the initiation of a petty cash request.

1. **User Task: Petty Cash Request**: This task uses a form to collect petty cash requests, including the requested amount and the reason for the request.

    ![Lanes and Pools Example](images/lanes_pools_example_2.png)

The process transitions from the Requester Lane to the Cashier Lane within the Cashier Pool for approval.

1. **User Task: Approve Petty Cash**: In this task, cashiers review and approve the petty cash request, recording the approver’s name for accountability.

    ![Lanes and Pools Example](images/lanes_pools_example_3.png)

After approval, the workflow returns to the Requester Lane for final confirmation and display of the approval outcome.

1. **Manual Task: Display Output**:

**Display Message**:

```markdown
Your petty cash request for {{amount}} has been approved by {{approved_by}}
```

This message informs the requester of the approval status, including the approved amount and the name of the approver.
After the manual task, marks the end of the process.

![Lanes and Pools Example](images/lanes_pools_example_4.png)

This BPMN diagram effectively uses Lanes and Pools to structure a petty cash request process, ensuring that responsibilities are clearly assigned and the workflow is logically organized.

## Managing Approval Processes for Designated Group Users

One common requirement in workflow management is creating an approval process where any user can initiate a request, but only a designated group can grant approval.
A specific challenge arises when the initiator is also a member of the approval group and should not approve their own request.

Let's consider a typical approval process where:

- Any user can start a request.
- A specific group ("approvers") can grant approval.
- The initiator, if part of the approvers, should not approve their own request.

### Solution

Implement a script task within the workflow to dynamically adjust the assignment of approval tasks, ensuring the initiator cannot approve their own request.

Insert a script task before the approval task to dynamically define and adjust the lane owners based on the current process context.

Use process data to identify group members eligible for approval tasks and exclude the initiator from this group.

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

This solution automatically adjusts the approvers list to exclude the initiator, maintaining the integrity of the approval process.

---
## Assigning Lane Owners

Assigning lane owners correctly in BPMN workflows is important for ensuring that tasks are routed to the appropriate personnel or departments within an organization.

Let's discuss the methods for assigning lane owners:

### Methods to Assign Lane Owners:

1. **Using Script Tasks**:
   - Script tasks enable dynamic assignment of lane owners within the workflow. You can specify the lane owners directly in the workflow logic, ensuring that tasks are routed correctly based on current operational needs or specific conditions.
   - **Example**:
     ```python
     # Script task to assign lane owners
     lane_owners = {
         "Reviewer": ["user1@example.com", "user2@example.com"]
     }
     ```
   - This script explicitly sets who the lane owners are for the 'Reviewer' lane. The names provided in the dictionary map directly to the users responsible for this lane.

2. **Assigning User Groups**:
   - In cases where script tasks are not used for direct assignments, lane owners can be specified by utilizing predefined user groups within DB.
   - **How to Configure User Groups**:
     - User groups can be assigned in the system configuration, often in a YAML file, which defines which users belong to specific groups. More information is available [in the admins and permissions section](https://spiff-arena.readthedocs.io/en/latest/DevOps_installation_integration/admin_and_permissions.html#setting-up-admin-in-config-yaml).

     - **Example YAML Configuration**:
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
   - This configuration shows how different user roles, such as admins and reviewers, are populated with specific users.

### Practical Application in a BPMN Model:

In a typical BPMN workflow, lane assignments are crucial for managing who performs various tasks within the process.
For example, a process might involve several departments or roles, each represented by a lane in the workflow model.

- **Process Start**
  - The process begins and an initial script task sets the lane owners. The BPMN model below effectively demonstrates a comprehensive workflow leading to a dynamic assignment of reviewers in the "Script Task: Get Reviewers".

![Lane Owners](images/lane_owners.png)

- **Task Execution**:
  - As tasks are executed, the workflow engine checks the `lane_owners` dictionary to determine which users are responsible for tasks in specific lanes.
  - If a lane owner is not set using a script task and no explicit assignment is provided, the engine queries the group name to determine potential task owners from DB.

```{admonition} Note
⚠ Specifying a user group in the `lane_owners` dictionary in a script task does not require it to previously exist in the database.
```
