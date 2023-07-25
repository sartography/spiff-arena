# Complete Task on Behalf of another User

| ⚙ How do I get there \| Menu Hierarchy |
| -------------------------------------- |
| Follow steps to [find a Process Instance](../spiffsparkles/find_a_process_instance.md)|

A task is assigned to a user who is responsible for completing it. However, due to various reasons, the user may find themselves unable to finish the task within the designated time frame. In such situations, the instance can be completed **by you on behalf of the user.** This enables a smooth continuation of the process from the initial user's perspective, allowing them to move on to the next task when they are ready.

## Complete Task assigned to a different user

> **Step 1: Find 'Process Instance'**

- The process instance will be assigned to another user and the task can be found by seraching for the Id in the ['Find By Id'](../spiffsparkles/find_a_process_instance.md) tab.

![assigned_to_me](images/assigned_to_me.png)

> **Step 2: Navigate to the Active Process Id**

Follow steps to [navigate to the Active Process Instance.](../spiffsparkles/navigate_to_an_active_process_instance.md)


```{admonition} Note
⚠ The task needs to be active for you to complete it. Completed process instances can not be edited or modified.
```

> **Step 3: Suspend the Process Instance**

Follow steps to [suspend process.](../spiffsparkles/suspend_resume_terminate)

```{admonition} Note
⚠ Note: Only Admin users will be able to complete this step.
```

> **Step 4: Edit selected Task**

- Click on the active task, which is highlighted in yellow. 
- Select "Edit" from the pop-up screen. A window, or code editor, will open up displaying the task data. Here, you can both view and edit the data as needed. For this step in the process, it's important to know which task data variables you need to change. This knowledge is necessary to ensure that the correct data is modified and the process continues as expected.

> **Step 5: Save Instance**

- Click "Save" to apply field changes to the Instance.

> **Step 6: Execute Task**

- Select to "Execute Task". This will execute the user task with applied changes.

> **Step 7: "Resume" process instance.**

- Follow steps to [resume process.](../spiffsparkles/suspend_resume_terminate)

> **Step 8: Refresh page**

- After a few seconds, refresh the page to ensure that the workflow has progressed to the next activity

| ✅ Success                                                    | 🚫 Error                                                      |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| The system will then display the parent process that contains the active instance searched for. | What if this was not successful. Add section to troubleshoot?
