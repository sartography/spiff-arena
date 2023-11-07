# Data Objects

In BPMN (Business Process Model and Notation), a data object represents the information or data used and produced by activities within a business process. It represents the data elements or artifacts that are relevant to the process and provides a way to model the flow of data through the process.
They help in clarifying the data flow and dependencies within the process, making it easier to understand how information is utilized and transformed throughout the process execution.

**Reasons to use data objects:**

- To represent and manage data within a business process. 
  
- When it is required to make a specific reference to data being used.
  
- When there are dependencies between tasks or activities based on shared data.

- When data changes within a process.

- If data needs to be stored or retrieved for use in a process.

## Data Object Types

### Data Object

![data_input](images/data_input.png) 

Represents the data or information that is required as an input to initiate or execute a particular task or process. BPMN input defines the data elements that need to be provided or available for the task to be performed.

### Data Output

![data_output](images/data_output.png)

Signifies the data or information that is generated or produced as a result of executing a task or process. BPMN output describes the data elements that are produced or modified during the execution of the task. 

### Data Object Reference

![data_object_reference](images/data_object_reference.png)

A Data Object in BPMN typically represents a specific piece of information or a data entity that is exchanged or manipulated during the course of a business process. It can represent both physical and digital data. Examples of Data Objects include documents, forms, reports, databases, or any other data entity relevant to the process. 

## Data Input Configuration

| 💻 Form | ⌨ Field Input | 📝 Description |
| --- | --- | --- |
| ![name_field](images/name_field.png) | **Name:** Update Customer Information | An identifier used to uniquely identify the element within the BPMN model. |
| ![id_field](images/id_field.png) | **ID:** Example - updateCustomerInformation | A descriptive name given to the element, providing a human-readable label or title. |
| ![name_field](images/documentation_field.png) | **Element Documentation:** URL, Raw Data, Plain Text | Additional information or documentation related to the element, such as URLs, plain text, or raw data. |
| ![name_field](images/data_object_prop.png) | **Element Documentation:** inventory_items| Enter an existing data object ID |
