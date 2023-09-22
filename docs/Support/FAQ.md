# Frequently Asked Questions
## Support and Administration

### **1. Running SpiffWorkflow in PyCharm**
**Q:** Is there a setup where I can run it within PyCharm?  
**A:** Yes, you can run SpiffWorkflow within PyCharm. For detailed settings, refer to the provided screenshot of flask server details. 

![Flask](images/Flask.png)

### **2. Adding Python Libraries to Spiff Workflow**
**Q:** Is there documentation available for adding python libraries to Spiff Workflow? For example, if I want to run a process to send emails, I would need `smtplib`.  
**A:** The default answer for something like sending emails would be to use a service task. We have an SMTP connector designed for this purpose. If you're using Spiff Arena, a connector proxy can provide a nice integration into the UI. Here are some helpful links:
- [SMTP Connector](https://github.com/sartography/connector-smtp)
- [Spiff-Connector Demo](https://github.com/sartography/connector-proxy-demo)
- [BPMN,DMN samples for Spiff-workflow-webapp](https://github.com/sartography/sample-process-models/tree/jon/misc/jonjon/smtp)

### **3. Tutorials on Using Spiff Workflow**
**Q:** Are there any tutorials available on how to use Spiff workflow?  
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

### **8. Integrating Workflow with External Python Code**
**Q:** How do you integrate your workflow with another python code?  
**A:** You can use script tasks to execute python code inside your workflow, or you can write services that can be called via service tasks.

### **9. Using Call Activity for Preconfigured Subprocesses**
**Q:** I need my users to generate many BPMN workflows by dropping preconfigured subprocesses into their workflows. Is this possible?  
**A:** Yes, you can use a "Call Activity" in SpiffArena to reference other processes in your diagram. SpiffArena provides a way to search for other processes in the system that can be used as Call Activities.

### **10. Integrating SpiffWorkflow with External Role Management**
**Q:** How do I interface permissions on a task from an external application user roles (ids)?  
**A:** You can manage the roles externally and pass in the user and group information, then assign them to the Lanes in your BPMN diagram.

### **11. Understanding Workflow Data vs Task Data**
**Q:** What is the difference between the `workflow.data` and `task.data`?  
**A:** Task data is stored on each task, and each task has its own copy. Workflow data is stored on the workflow. If you use BPMN DataObjects, that data is stored there.

### **12. Understanding Secrets and Authentications in SpiffArena**
**Q:** What are 'Secrets' and 'Authentications' used for in SpiffArena?  
**A:** Secrets are used for communicating with external services when you use service tasks and connectors. Authentications are used when you need to OAuth into an external service. Check out more information [here](https://spiff-arena.readthedocs.io/en/latest/DevOps_installation_integration/Secrets.html).

### **13. Determining the Lane of a Task in a Workflow**
**Q:** In the pre/post script of a task in a workflow, how do I determine what lane the current task is in?  
**A:** You can access the task and use `task.task_spec.lane` to get the lane as a string.

### **14. Understanding Script Attributes Context**
**Q:** I'm trying to understand the details of `script_attributes_context`. Where can I find more information?  
**A:** The `ScriptAttributesContext` is defined [here](https://github.com/sartography/spiff-arena/blob/deploy-mod-prod/spiffworkflow-backend/src/spiffworkflow_backend/models/script_attributes_context.py#L9).

### **15. Using Message Start Event to Kick Off a Process**
**Q:** How do I use a message start event to kick off a process?  
**A:** This [script](https://github.com/sartography/spiff-arena/blob/main/spiffworkflow-backend/bin/run_message_start_event_with_api#L39) is an example of using a message start event to kick off a process.


### **16. Making REST API Calls in SpiffArena**
**Q:** How do I make REST API calls in SpiffArena?  
**A:** You can use Service Tasks driven by a Connector Proxy. Check out the [Connector Proxy Demo](https://github.com/sartography/connector-proxy-demo) for more details.

### **17. Integrating Workflow with External Python Code**
**Q:** How do I integrate my workflow with another python code?  
**A:** You can use script tasks to execute python code inside your workflow or write services that can be called via service tasks.

### **18. Using Call Activity for Preconfigured Subprocesses**
**Q:** Can I use preconfigured subprocesses in my workflows?  
**A:** Yes, you can use a "Call Activity" in SpiffArena to reference other processes in your diagram.

### **20. Assigning User Tasks in SpiffWorkflow**
**Q:** How does one use camunda:assignee="test" in a userTask with Spiff?  
**A:** In SpiffWorkflow, user task assignments can be managed using Lanes in your BPMN diagram. Each Lane can designate which individual or group can execute the tasks within that Lane. If you're looking to interface permissions based on external application user roles, you can manage roles externally and pass the user and group information to assign them to the Lanes.

### **21. Mimicking an Inclusive Gateway in SpiffWorkflow**
**Q:** How can we mimic an inclusive gateway since SpiffWorkflow doesn't support it?  
**A:** You can work around the absence of an inclusive gateway in SpiffWorkflow by using a Parallel Gateway. Within each path following the Parallel Gateway, you can place an Exclusive Gateway to check for the conditions that are or are not required. This approach is effective if the flows can eventually be merged back together.

![Mimicking Inclusive Gateway](images/Mimicking_inclusive_gateway.png)

### **22. Designing an Approval Process in SpiffWorkflow**
**Q:** I am designing an approval process using spiff-workflow. Can SpiffWorkflow handle scenarios where a task should complete if more than 2 users approve out of 3 assignees?  
**A:** Yes, SpiffWorkflow can handle complex approval processes. The [provided video](https://www.youtube.com/watch?v=EfTbTg3KRqc) link offers insights into managing such scenarios using SpiffWorkflow.

### **23. Determining the Lane of a Task in SpiffWorkflow**
**Q:** How do I determine what lane the current task is in during a pre/post script of a task in a workflow?  
**A:** In SpiffWorkflow, you can determine the lane of a task by accessing the task's properties. Specifically, you can use `task.task_spec.lane` to retrieve the lane as a string. This allows you to programmatically determine which lane a task belongs to during its execution.


### **24. Using Call Activity for Modular Workflows**
**Q:** Can I create modular workflows using preconfigured subprocesses in SpiffWorkflow?  
**A:** Absolutely! SpiffWorkflow supports the use of "Call Activity", which allows you to reference other processes in your workflow. This means you can create modular workflows by designing subprocesses (like 'send to accounts') and then incorporating them into multiple main workflows as needed. This modular approach not only streamlines the design process but also ensures consistency across different workflows.

### **25. Integrating SpiffWorkflow with Other Python Code**
**Q:** How do you integrate your workflow with another python code?  
**A:** Integrating SpiffWorkflow with other Python code is straightforward. You have two primary methods:
1. **Script Tasks**: These allow you to execute Python code directly within your workflow. This method is suitable for simpler integrations where the code logic is not too complex.
2. **Service Tasks**: For more complex integrations, you can write services that can be called via service tasks within your workflow. This method provides more flexibility and is ideal for scenarios where you need to interface with external systems or perform more intricate operations.
