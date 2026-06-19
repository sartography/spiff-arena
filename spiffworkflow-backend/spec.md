allowing sending email on user task available

how? via per-task process model

allow a configuration on each user task that indicates the process model that should be run when the user task becomes available. inject into the process instance all of the information that might be useful to someone implementing a custom process model. It might be nice to send an email to the potential owners of the user task, so providing the full url to the user task including the frontend url, the process instance, and the task guid, would be nice. Perhaps also the programmatic path to submit the task via the API? perhaps the potential owner usernames or emails or user ids? do we already have a script to get a user from a primary key id that could be used in a process model? should it be a dictionary with key/value pairs or just a bunch of scaler variables like task_url and process_instance_id?

probably the process model should not start with a message start event, but just a normal none start event. then we can have code that "manually" injects the variables they might need.
