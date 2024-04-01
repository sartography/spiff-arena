# Data Stores

![data_store](images/data_store.png)

A Data Store is a BPMN construct that represents a storage location where data is stored, retrieved, and can be accessed among multiple process instances, including different process models.
It can represent a database, a file system, or any other storage mechanism.

## When to use

You might use a Data Store when it is not sufficient for data to be accessible in just a single process instance, but it needs to be shared across different process instances.
If you have a use case where you need to store data and access it from multiple different process instances, you could also consider using a Service Task to contact a database external to SpiffWorkflow, either via a database library in a connector or using a database via an API.
All of these mechanisms work well in SpiffWorkflow, so the choice will depend on your storage and performance requirements.
