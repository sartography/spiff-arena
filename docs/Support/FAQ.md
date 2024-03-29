# Frequently Asked Questions
## Support and Administration

### **1. Running SpiffWorkflow in PyCharm**
**Q:** Is there a setup where I can run it within PyCharm?
**A:** Yes, you can run SpiffWorkflow within PyCharm. For detailed settings, refer to the provided screenshot of Flask server details.

![Flask](images/Flask.png)

### **2. Adding Python Libraries to SpiffWorkflow**
**Q:** Is there documentation available for adding Python libraries to SpiffWorkflow? For example, if I want to run a process to send emails, I would need `smtplib`.
**A:** The default answer for something like sending emails would be to use a service task. We have an SMTP connector designed for this purpose. If you're using Spiff Arena, a connector proxy can provide a nice integration into the UI. Here are some helpful links:
- [SMTP Connector](https://github.com/sartography/connector-smtp)
- [Spiff-Connector Demo](https://github.com/sartography/connector-proxy-demo)
- [BPMN, DMN samples for SpiffWorkflow](https://github.com/sartography/sample-process-models/tree/jon/misc/jonjon/smtp)

### **3. Tutorials on Using SpiffWorkflow**
**Q:** Are there any tutorials available on how to use SpiffWorkflow?
**A:** Yes, here are some references:
- [SpiffExample CLI](https://github.com/sartography/spiff-example-cli)
- [SpiffArena Documentation](https://spiff-arena.readthedocs.io/)
- [SpiffWorkflow Documentation](https://spiffworkflow.readthedocs.io/en/stable/index.html)
- [Getting Started with SpiffWorkflow](https://www.spiffworkflow.org/posts/articles/get_started/)

### **4. Understanding Task Data in Custom Connectors**
**Q:** What kind of data can I expect from `task_data`?
**A:** The `task_data` param contains data comprised of variables/values from prior tasks. For instance, if you have a script task before your service task that sets `x=1`, then in the `task_data` param, you should see `{"x": 1}`.

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
**Q:** How do you integrate your workflow with another Python code?
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
**Q:** In the pre/post script of a task in a workflow, how do I determine what lane the current
