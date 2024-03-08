# Error Events

Error Events in Business Process Model and Notation (BPMN) are pivotal in managing exceptions and errors that occur within business process workflows. These events enable processes to handle errors gracefully, ensuring that workflows are robust, resilient, and capable of addressing unforeseen issues efficiently.
 Below, we delve into the types of Error Events, offering definitions and enriched context for their practical applications.

## Types of Error Events

### 1. Error Start Event

![Error Start Event](images/error-events1.png)

The Error Start Event triggers the start of a subprocess in reaction to an error identified in a different process or subprocess. It is a specialized event used to initiate error handling workflows dynamically.

**Reason to Use**: 
- **Modular Error Handling**: Separates error handling logic into dedicated subprocesses, improving process organization and maintainability.
- **Reusability**: Allows for the reuse of error handling subprocesses across multiple parent processes.
- **Focused Recovery Strategies**: Enables the development of targeted recovery strategies for specific errors, enhancing error resolution effectiveness.

**Example**: 

![](images/Start_event_error_example.png)

In an automated supply chain system, an Error Start Event initiates a "Supplier Notification" subprocess when inventory restocking fails due to supplier issues, triggering actions such as alternative supplier selection and impact analysis.

```{admonition} Note
⚠ The start event needs to be in an **event sub process** to be selected.