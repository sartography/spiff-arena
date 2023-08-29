(process_error_handling)=
# Process Error Handling

What happens when a process model errors?
The system will capture the error and cause a process model to run.
In order to get started, simply create a process model that includes a message start event that handles messages with the name `SystemErrorMessage`.
You can use this process model to handle the error in whatever way is most helpful for you.

Process models often have ways to communicate with users--using an email connector if you use email or using a slack connector if you use slack, etc--and you can use these same capabilities to inform the appropriate users when an error occurs.
You can decide to ignore errors that occur in less important models and you can escalate errors in other models to the CEO.
Since you are using a process model, you have all of the power you need to handle errors in the way that matches your business requirements.
