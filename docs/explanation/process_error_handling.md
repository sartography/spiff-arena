(process_error_handling)=
# Process Error Handling

What happens when a process model errors out?
The system will capture the error and trigger a process model to run.
To get started, simply create a process model that includes a message start event that handles messages with the name `SystemErrorMessage`.
You can use this process model to handle the error in whatever way is most beneficial for you.

Process models often have ways to communicate with users--using an email connector if you use email, or a Slack connector if you use Slack, etc.--and you can use these same capabilities to inform the appropriate users when an error occurs.
You can choose to ignore errors that occur in less important models, and you can escalate errors in other models to the CEO.
Since you are using a process model, you have all the power you need to handle errors in a way that matches your business requirements.
