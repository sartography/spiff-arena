# Build a purchase approval workflow

Let's build a full workflow.
Taking a standard purchase approval flow, we will create a working process.
The runnable process will collect the purchase details, allow for review, and show the review decision.

Allow about 30 minutes.

## Before you begin

- Sign in to Spiff Arena and open a playground or process group where you can create and edit models.
  If you need a workspace, follow the {ref}`QuickStart Guide <quickstart-create-process>`.
- You need permission to start processes and view your process instances.

You will play both requester and reviewer.
Without lanes, Arena assigns human tasks to the person who starts the process.
This example will not enforce independent approval, so if you want to approve your pony request, you can go right ahead.

## What you will build

A requester asks for a keyboard.
The reviewer chooses `approve` or `decline`.
An exclusive gateway takes one path, and a manual task displays the result before the process ends.

```{figure} /images/tutorials/purchase-approval-flow.svg
:alt: Start leads to Submit request, then Review request, then an exclusive gateway. The approve path leads to Show approval; the decline path leads to Show decline. Both paths end.
:width: 720px

This is a simplified SVG diagram.
```

A user task collects form data.
A manual task can display instructions and wait for someone to click **Continue**.
The gateway reads the reviewer's choice.

## 1. Create the model

1. Open **Processes**, enter your playground or process group, and add a process model.
2. Set **Display Name** to `Purchase approval` and **Identifier** to `purchase-approval`.
3. Submit the form, then open the model's **Files** tab.
4. Open the generated BPMN file.

You can [download the finished files](#finished-example-files) for reference.

## 2. Draw the steps

Use the editor's palette and the append controls beside a selected shape.
To change a task's type, select it and use the wrench menu.
Remove the generated example task and any connections you no longer need; keep one start event and one end event.

Add these elements and name them by double-clicking each shape, or with **Name** in the properties panel:

| Type | Name |
| --- | --- |
| User Task | Submit request |
| User Task | Review request |
| Exclusive Gateway | Decision? |
| Manual Task | Show approval |
| Manual Task | Show decline |

Connect the start event to **Submit request**, then **Review request**, then **Decision?**.
Draw two outgoing sequence flows from the gateway, one to each manual task.
Connect both manual tasks to the end event.

Leave pools and lanes out of this first version.
Select the canvas background and check that the process is **Executable**, then save the diagram.

## 3. Collect the request

Select **Submit request**.
In **Web Form (with Json Schemas)**, click **Launch Editor**, name the new form `purchase-request`, and click **Create Files**.
Replace the **JSON Schema** with:

```{literalinclude} examples/purchase-approval/purchase-request-schema.json
:language: json
```

Leave **UI Settings** as `{}`.
The form editor saves changes automatically.
Pause after your last edit to let the save finish, click **Close**, then save the BPMN diagram.
Check that **JSON Schema Filename** is `purchase-request-schema.json` and leave **Variable Name** empty.

The property names become task-data keys: `item`, `amount`, and `reason`.
The titles are the labels people see.
Leaving **Variable Name** empty keeps these keys at the top level, where the later instructions can read them.
The editor also creates an example-data file for previews; its contents are not submitted to a running process.

The form preview shows an item, a positive amount, and a reason.
The amount is a number, not text containing a currency symbol.

## 4. Review the request

Select **Review request**.
Launch its form editor, name the form `purchase-review`, click **Create Files**, and use this JSON Schema:

```{literalinclude} examples/purchase-approval/purchase-review-schema.json
:language: json
```

Again, leave **UI Settings** as `{}` and **Variable Name** empty.
Wait for the form changes to save, close the editor, and confirm that **JSON Schema Filename** is `purchase-review-schema.json`.

In this task's **Instructions**, enter:

```jinja
## Review this purchase

- **Item:** {{ item }}
- **Amount (USD):** {{ amount }}
- **Reason:** {{ reason }}

Choose approve or decline and explain your decision.
```

Arena renders these instructions with the data from **Submit request**.
The review form adds `decision` and `review_note`.
Save the diagram.

```{figure} /images/tutorials/purchase-approval-review.svg
:alt: Simplified review form. Instructions show a Keyboard request for 85 USD to replace a broken keyboard. Below are a Decision dropdown, a Review note field, and Submit.
:width: 480px

A sketch of the running task.
```

```{note}
Use a string choice for this decision, rather than a required checkbox.
Arena treats a required boolean checkbox as something the user must check, which is unsuitable for an approve-or-decline choice.
```

## 5. Route the decision

Select the **sequence flow** from **Decision?** to **Show approval**.
Name it `approve`.
In **Conditions**, set **Condition Expression** to:

```python
decision == "approve"
```

Select the other outgoing sequence flow, name it `decline`, and set its condition to:

```python
decision == "decline"
```

Both conditions are Python expressions.
Use `==` to compare values; the arrow's name alone does not control routing.
Keep both flows conditional, with neither marked as a default flow.
The required form choice supplies one of the two supported values.

```{figure} /images/tutorials/purchase-approval-condition.svg
:alt: A sequence flow named approve is selected between the Decision gateway and Show approval. Its Conditions panel contains the expression decision == "approve".
:width: 560px

Configure the outgoing arrow, not the gateway.
```

## 6. Show and record the outcome

Select **Show approval** and enter these **Instructions**:

```jinja
## Purchase approved

Your request for {{ item }} (USD {{ amount }}) was approved.

Reviewer note: {{ review_note }}

Click Continue to finish this practice request. No order will be placed.
```

Under **Pre/Post Scripts**, set its **Post-Script** to:

```python
outcome = "approved"
```

For **Show decline**, use:

```jinja
## Purchase declined

Your request for {{ item }} (USD {{ amount }}) was declined.

Reviewer note: {{ review_note }}

Click Continue to finish this practice request.
```

Set that task's **Post-Script** to:

```python
outcome = "declined"
```

These scripts record which branch finished.
They run when the manual task completes, so the process waits for **Continue** before recording the outcome and reaching the end event.
Save the diagram.

## 7. Run both paths

Return to the model's **Files** tab.
Check that your BPMN file is marked **Primary File**; use **Set As Primary File** if needed.
Click **Start** to create a new instance.

1. Submit `Keyboard`, `85`, and `Replace a broken keyboard` in the request form.
2. Check that the review instructions show those values.
3. Choose `approve`, enter `Within budget` as the review note, and submit.
4. Check that **Purchase approved** appears, then click **Continue**.
5. Open the model's **My process instances** tab and inspect the completed instance.
   In its diagram, the approval task should be completed and the decline task should not have run.

Start a **new instance** and repeat with `decline` and `Use the spare keyboard`.
This time you should see **Purchase declined**.
Click **Continue** and inspect that instance's diagram too.

Each instance keeps its own request data and decision.

## If something differs

| Symptom | Check |
| --- | --- |
| No Start button | The BPMN file must be primary and its process executable. Your account also needs permission to start it. |
| The review task has no form | Select the task and check **JSON Schema Filename**. Both schema files must be in this process model. |
| Request details are blank in the instructions | Check the schema property names and leave **Variable Name** empty on both user tasks. Start a new instance after saving a correction. |
| The gateway reports an error | Check both outgoing conditions and the lowercase `approve` / `decline` choices. Conditions belong on the arrows. |
| The process is still waiting | Click **Continue** on the result task. Reaching that screen does not complete it. |

## Finished example files

Download each file and upload it **one at a time** through the model's **Upload File** control:

- {download}`purchase-approval.bpmn <examples/purchase-approval/purchase-approval.bpmn>`
- {download}`purchase-request-schema.json <examples/purchase-approval/purchase-request-schema.json>`
- {download}`purchase-request-uischema.json <examples/purchase-approval/purchase-request-uischema.json>`
- {download}`purchase-review-schema.json <examples/purchase-approval/purchase-review-schema.json>`
- {download}`purchase-review-uischema.json <examples/purchase-approval/purchase-review-uischema.json>`

Keep the downloaded filenames unchanged and set `purchase-approval.bpmn` as the primary file.
The two UI schema files contain `{}`, which selects the default form controls.

## Next: give the review to someone else

A real approval workflow also needs a separate reviewer and appropriate permissions.

Continue with [Assigning Tasks to People](/how_to_guides/building_diagrams/assigning_tasks_to_people): put **Review request** in a reviewer lane, and put the request and result tasks in a `process_initiator` lane.
Configure the reviewer lane's owners and confirm that a second account can complete the review while the requester cannot.
See [Manage Permissions](/how_to_guides/deployment/manage_permissions) for access configuration.
