# Learn the Basics

## BPMN and SpiffWorkflow

Business Process Model and Notation (BPMN) is a diagramming language for specifying business processes. BPMN links the realms of business and IT, and creates a common process language that can be shared between the two.

BPMN describes details of process behaviors efficiently in a diagram. The meaning is precise enough to describe the technical details that control process execution in an automation engine. SpiffWorkflow allows you to create code to directly execute a BPMN diagram.

<<<<<<< HEAD
When using SpiffWorkflow, a client can manipulate the BPMN diagram and still have their product work without a need for you to edit the Python code, improving response and turnaround time.

## BPMN Elements

### Tasks

### Gateways

### Events
=======
When using SpiffWorkflow, a client can create the BPMN diagram and still have their product work without a need for you to edit the Python code, improving response and turnaround time.


## BPMN Elements
BPMN (Business Process Model and Notation) elements are the building blocks used to model business processes visually. They represent different aspects of a process, such as tasks, events, gateways, and flows, and are used to describe the flow of activities, decisions, and data within a process.

### Tasks
Tasks represent activities or work that needs to be performed as part of a process. They can be manual tasks that require human intervention or automated tasks that are executed by systems or applications.

| **Element**   | **Symbol**                                                | **Description**                                                                                                                                                                                    |
|---------------|------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Service       | <div style="width:100px"></div> ![Untitled](images/04-BPMN-Service-Task.png)       | Task that uses a Web service, an automated application, or other kinds of service in completing the task.                                                                                          |
| Send          | <div style="width:100px"></div>![Untitled](images/06-BPMN-Send-Task.png)          | Task that sends a Message to another pool. The Task is completed once the Message has been sent.                                                                                                   |
| Receive       | <div style="width:100px"></div>![Untitled](images/23-BPMN-Receive-Task.png)       | A Receive Task indicates that the process has to wait for a message to arrive in order to continue. The Task is completed once the message has received.                                           |
| User          | ![Untitled](images/08-BPMN-User-Task.png)          | A User Task represents that a human performer performs the Task with the use of a software application.                                                                                            |
| Manual        | ![Untitled](images/10-BPMN-Manual-Task.png)        | A Manual Task is a Task that is performed without the aid of any business process execution engine or any application.                                                                             |
| Business Rule | ![Untitled](images/12-BPMN-Business-Rule-Task.png) | Business Rule Task is newly added in BPMN 2.0. It provides a mechanism for a process to provide input to a Business Rules Engine and then obtain the output provided by the Business Rules Engine. |
| Script        | ![Untitled](images/14-BPMN-Script-Task.png)        | A Script Task is executed by a business process engine. The task defines a script that the engine can interpret.                                                                                   |                                                                |


### Gateways
Gateways represent decision points in a process. They determine which path the process will take based on certain conditions or rules. There are different types of gateways, such as exclusive gateways (XOR), inclusive gateways (OR), and parallel gateways (AND).

### Flows
Flows represent the sequence or direction of activities in a process. There are different types of flows in BPMN, including sequence flows, message flows, and association flows. Sequence flows indicate the order in which tasks are performed, message flows represent the exchange of messages between participants, and association flows connect data objects or artifacts to activities.

### Artifacts
Artifacts are used to provide additional information or documentation within a process. They include data objects (representing information or data needed for the process), annotations (providing explanatory or descriptive text), and groups (used to visually group related elements).

[def]: images/Untitled_2.png
>>>>>>> origin/main
