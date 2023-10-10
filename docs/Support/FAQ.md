# Frequently Asked Questions
## Support and Administration

### **1. Running SpiffWorkflow in PyCharm**
**Q:** Is there a setup where I can run it within PyCharm?  
**A:** Yes, you can run SpiffWorkflow within PyCharm. For detailed settings, refer to the provided screenshot of flask server details. 

![Flask](images/Flask.png)

### **2. Adding Python Libraries to SpiffWorkflow**
**Q:** Is there documentation available for adding python libraries to SpiffWorkflow? For example, if I want to run a process to send emails, I would need `smtplib`.  
**A:** The default answer for something like sending emails would be to use a service task. We have an SMTP connector designed for this purpose. If you're using Spiff Arena, a connector proxy can provide a nice integration into the UI. Here are some helpful links:
- [SMTP Connector](https://github.com/sartography/connector-smtp)
- [Spiff-Connector Demo](https://github.com/sartography/connector-proxy-demo)
- [BPMN,DMN samples for SpiffWorkflow](https://github.com/sartography/sample-process-models/tree/jon/misc/jonjon/smtp)

### **3. Tutorials on Using SpiffWorkflow**
**Q:** Are there any tutorials available on how to use SpiffWorkflow?  
**A:** Yes, here are some references:
- [SpiffExample CLI](https://github.com/sartography/spiff-example-cli)
- [SpiffArena Documentation](https://spiff-arena.readthedocs.io/)
- [SpiffWorkflow Documentation](https://spiffworkflow.readthedocs.io/en/stable/index.html)
- [Getting Started with SpiffWorkflow](https://www.spiffworkflow.org/posts/articles/get_started/)

### **4. Understanding Task Data in Custom Connectors**
**Q:** What kind of data can I expect from `task_data`?  
**A:** The `task_data` param contains data comprised of variables/values from prior tasks. For instance, if you have a script task before your service task that set `x=1`, then in the `task_data` param, you should see `{"x": 1}`.

### **5. Understanding and Using Custom Connectors**
**Q:** What are custom connectors and how do I use them?  
**A:** Custom connectors in SpiffWorkflow allow for integration with external systems or services. They enable the workflow to interact with other platforms, fetch data, or trigger actions. To use them, you'll typically define the connector's behavior, specify its inputs and outputs, and then use it within your BPMN process as a service task.

### **6. Using Data Object Reference and Data Store Reference**
**Q:** What are some good references for "Data Object Reference" and "Data Store Reference" in SpiffWorkFlow?  
**A:** Here are some references to help you understand and implement "Data Object Reference" and "Data Store Reference" in SpiffWorkflow:
- [Understanding BPMN's Data Objects with SpiffWorkflow](https://medium.com/@danfunk/understanding-bpmns-data-objects-with-spiffworkflow-26e195e23398)
- [Data Encapsulation with SpiffWorkflow Video](https://youtu.be/0_PgaaI3WIg)

### **7. Resetting a Workflow**
**Q:** Is there a way of "resetting" a workflow without reloading the BPMN and DMN files?  
**A:** Yes, you can reset a workflow using the following code:
```python
start = workflow.get_tasks_from_spec_name('Start')[0]
workflow.reset_from_task_id(start.id)
```

### **8. Integrating SpiffWorkflow with other Python code**
**Q:** How do you integrate your workflow with another python code?  
**A:** Integrating SpiffWorkflow with other Python code is straightforward. You have two primary methods:
1. **Script Tasks**: These allow you to execute Python code directly within your workflow. This method is suitable for simpler integrations where the code logic is not too complex.
2. **Service Tasks**: For more complex integrations, you can write services that can be called via service tasks within your workflow. This method provides more flexibility and is ideal for scenarios where you need to interface with external systems or perform more intricate operations.

### **9. Using Call Activity for preconfigured modular subprocesses**
**Q:** I need my users to generate many BPMN workflows by dropping preconfigured subprocesses into their workflows. Is this possible?  
**A:** Yes, you can use a "Call Activity" in SpiffArena to reference other processes in your diagram. SpiffArena provides a way to search for other processes in the system that can be used as Call Activities. This means you can create modular workflows by designing subprocesses (like ‘send to accounts’) and then incorporating them into multiple main workflows as needed. This modular approach not only streamlines the design process but also ensures consistency across different workflows.

### **10. Integrating SpiffWorkflow with External Role Management**
**Q:** How do I make external application user roles affect permissions on a task?  
**A:** You can manage the roles externally in an OpenID system and access the user and group information in the Lanes of your BPMN diagram.

### **11. Understanding Workflow Data vs Task Data**
**Q:** What is the difference between the `workflow.data` and `task.data`?  
**A:** Task data is stored on each task, and each task has its own copy. Workflow data is stored on the workflow. If you use BPMN DataObjects, that data is stored in workflow data.

### **12. Understanding Secrets and Authentications in SpiffArena**
**Q:** What are 'Secrets' and 'Authentications' used for in SpiffArena?  
**A:** Secrets are used for communicating with external services when you use service tasks and connectors. Authentications are used when you need to OAuth into an external service. Check out more information [here](https://spiff-arena.readthedocs.io/en/latest/DevOps_installation_integration/Secrets.html).

### **13. Determining the Lane of a Task in a Workflow**
**Q:** In the pre/post script of a task in a workflow, how do I determine what lane the current task is in?  
**A:** You can access the task and use `task.task_spec.lane` to get the lane as a string. This allows you to programmatically determine which lane a task belongs to during its execution.

### **14. Understanding Script Attributes Context**
**Q:** I'm trying to understand the details of `script_attributes_context`. Where can I find more information?  
**A:** The `ScriptAttributesContext` class is defined [here](https://github.com/sartography/spiff-arena/blob/deploy-mod-prod/spiffworkflow-backend/src/spiffworkflow_backend/models/script_attributes_context.py#L9).

### **15. Using Message Start Event to Kick Off a Process**
**Q:** How do I use a message start event to kick off a process?  
**A:** This [script](https://github.com/sartography/spiff-arena/blob/main/spiffworkflow-backend/bin/run_message_start_event_with_api#L39) is an example of using a message start event to kick off a process.


### **16. Making REST API Calls in SpiffArena**
**Q:** How do I make REST API calls in SpiffArena?  
**A:** You can use Service Tasks driven by a Connector Proxy. Check out the [Connector Proxy Demo](https://github.com/sartography/connector-proxy-demo) for more details.

### **17. Assigning User Tasks in SpiffWorkflow**
**Q:** How does one use camunda:assignee="test" in a userTask with Spiff?  
**A:** In SpiffWorkflow, user task assignments can be managed using Lanes in your BPMN diagram. Each Lane can designate which individual or group can execute the tasks within that Lane. If you're looking to interface permissions based on external application user roles, you can manage roles externally and pass the user and group information to assign them to the Lanes.

### **18. Mimicking an Inclusive Gateway in SpiffWorkflow**
**Q:** How can we mimic an inclusive gateway since SpiffWorkflow doesn't support it?  
**A:** You can work around the absence of an inclusive gateway in SpiffWorkflow by using a Parallel Gateway. Within each path following the Parallel Gateway, you can place an Exclusive Gateway to check for the conditions that are or are not required. This approach is effective if the flows can eventually be merged back together.

![Mimicking Inclusive Gateway](images/Mimicking_inclusive_gateway.png)

### **19. Designing an Approval Process in SpiffWorkflow**
**Q:** I am designing an approval process using SpiffWorkflow. Can SpiffWorkflow handle scenarios where a task should complete if more than 2 users approve out of 3 assignees?  
**A:** Yes, SpiffWorkflow can handle complex approval processes. The [provided video](https://www.youtube.com/watch?v=EfTbTg3KRqc) link offers insights into managing such scenarios using SpiffWorkflow.



**20: I restarted docker-compose, and my process instances in Spiff Arena aren't persistent. How can I ensure they remain after a restart?**

**A:** Make sure you're using the updated "getting started" `docker-compose.yml` file that uses sqlite to persist the database between docker compose restarts.
This will ensure that your process instances remain after a restart.

If you're still facing issues, refer to the provided documentation on admin and permissions for further guidance.

**21: Is it possible to download a process model in Spiff Arena and then re-upload it?**

**A:** Yes, in Spiff Arena, you can download a process model and then re-upload it. However, it's essential to note that all process IDs must be unique across the system. If you're re-uploading a process model, its ID might need to be modified to ensure uniqueness.

**22: What are the "notification addresses" and "metadata extractions" fields when creating a new process model in Spiff Arena?**

**A:** When creating a new process model in Spiff Arena, the "notification addresses" field is used to specify recipients for notifications related to that process.
The "metadata extractions" field is used to extract specific metadata from the process.
Detailed documentation for both fields is available.
It's worth noting that the functionality of "Notification Addresses" might undergo changes in the future to centralize the logic and avoid splitting configurations.


**23: Why doesn't the Spiff Arena frontend always load completely?**

**A:** The issue might arise when the frontend cannot communicate with the backend.
Recent updates have been made to address this specific problem.
Previously, the backend could deadlock when it received a high number of concurrent requests, exhausting the available worker processes.

Since it uses built-in openid, each request would need to communicate with the backend itself.
This issue has been resolved in the newer versions. To potentially fix this, you can update your setup by running the following commands in the directory where you downloaded the `docker-compose.yml` file:

```
docker compose pull
docker compose down
docker compose up -d
```

By doing this, you'll pull the latest images, shut down the current containers, and then start them up again with the updated configurations.
This should help in ensuring that the frontend loads completely and communicates effectively with the backend.


**24: I'm using an M1/M2 Mac and facing issues with docker-compose in Spiff Arena. How can I resolve this?**

**A:** Ensure that you're using the latest versions of Docker and docker-compose.
If you encounter messages about platform mismatches, note that these may just be warnings and not errors.
Update your images and restart the containers as needed.
Instructions in the getting started guide reference `curl`, but if that is not working for you, `wget` may be an option that is already installed on your system.

**25: Why aren't timer events working in Spiff Arena, and how can they be fixed?**

**A:** Timer events in Spiff Arena require a specific syntax for their expressions.
For instance, the expression "R5/PT10S" should be quoted.
This is because the value needs to be derived from a valid Python expression.
Ensure that the background scheduler is running, as timers in Spiff Arena are controlled by it.

 If you're still facing issues, refer to the provided sample BPMN file and ensure that your timer expressions match the required format.

**26: Why can't I import an external module in a script task in Spiff Arena?**

**A:** In Spiff Arena, script tasks are designed for lightweight scripting and do not support importing external modules.
If you need to communicate with external systems, it's recommended to use a ServiceTask instead.
ServiceTasks in Spiff Arena utilize a concept called Connector Proxy, an externally hosted system that adheres to a specific protocol.
For tasks like checking if an API is functioning correctly, you can set up a Connector Proxy to handle the request.
Detailed documentation available [here](https://spiff-arena.readthedocs.io/en/latest/DevOps_installation_integration/configure_connector_proxy.html).
If you want to bypass security features of the restricted script engine and import modules from your script tasks, you can set the environment variable: `SPIFFWORKFLOW_BACKEND_USE_RESTRICTED_SCRIPT_ENGINE=false`
