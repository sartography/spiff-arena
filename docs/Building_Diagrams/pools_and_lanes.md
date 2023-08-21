# Pools and Lanes

A Pool represents a participant and can be seen as a self-contained process. This participant can be an internal entity (e.g., a department within a company) or an external entity (e.g., a customer or another company). Lanes are helpful in highlighting which specific role or department is responsible for certain activities or tasks in a process. A process can have one or more Pools, each with one or more Lanes.

**Reasons to Use Pools and Lanes:**

- They visually represent distinct participants in a process, such as various departments, organizations, or systems.
- Helps depict interactions between separate business entities, like a buyer-seller dynamic.
- Provide a clear overview of communication between different participants.
- Categorizing tasks or activities based on specific roles.
- Bring structure and organization to complex diagrams that involve multiple roles, departments, or stakeholders.

 
## Pools

A Pool can be configured as an "Empty Pool" (collapsed) or an "Expanded Pool". You can choose the desired configuration 🔧 from the element's options after dragging it onto your diagram.

![pools_and_lanes](images/pools_and_lanes.png) 

Empty Pools are used to represent role players in cases where a specific process is neither known nor required, but the interaction points remain valuable. They serve to illustrate the engagement of certain entities without detailing their internal processes, for example, we dont know a customers specific process but it matters when we interact with them to complete our process.

Conversely, Expanded Pools are employed when the processes are known and hold relevance within the diagram's context. 

## Lanes

Lanes group activities within a single Pool, usually signifying different roles or departments. 

![lanes](images/lanes.png)

Lanes are incorporated into Pools when the roles they represent belong to the same entity. However, if a process doesn't logically fit within the same Pool, like those for different organizations or businesses, it's more appropriate to represent it as a separate Pool rather than another Lane.

![lanes](images/separate_pools.png)

## Configuration

![participant_configuration](images/participant_configuration.png)

**Collapsed (Empty) Pool configuration:**

Configuring an "Empty Pool" (collapsed) representing an external entity such as a customer.

| 💻 Form | ⌨ Field Input | 📝 Description |
| --- | --- | --- |
| ![participant_sales](images/participant_customer.png) | **Participant Name:** Sales, **Participant ID:** sales, | A clear and descriptive name serves as a human-readable label or title the participant. Additionally, a unique ID is essential to distinguish the participant from other participants. |
| ![data_object_pools](images/data_object_pools.png) | **Data Objects:** order_details | Create or Refernce a Data Object to store information for sharing between entities. |

**Expanded Pool configuration:**

Setting up an "Expanded Pool" requires referencing the process, in contrast to the setup of an empty pool.

| 💻 Form | ⌨ Field Input | 📝 Description |
| --- | --- | --- |
| ![participant_sales](images/participant_sales.png) | **Participant Name:** Sales, **Participant ID:** sales,  **Process ID:** process_order, **Process Name:** Process Order | A clear and descriptive name serves as a human-readable label or title for both the participant and the process. Additionally, a unique ID is essential to distinguish both the participant and the process from others. |
| ![data_object_pools](images/data_object_pools.png) | **Data Objects:** order_details | Create or Refernce a Data Object to store information for sharing between entities. |

**Collapsed Pool configuration:**

![lanes](images/lane_configuration.png)

Remember that each pool requires Lane configuration, even if it contains just a single Lane.
![lanes](images/pool_settings.png)

| 💻 Form | ⌨ Field Input | 📝 Description |
| --- | --- | --- |
| ![participant_sales](images/participant_lane.png) | **Name:** Manager | A concise and descriptive label that accurately represents the owner and role of the Lane. |
| ![data_object_pools](images/data_object_pools.png) | **ID:** lane_manager | A distinct ID to differentiate each Lane, especially when there are multiple.|
