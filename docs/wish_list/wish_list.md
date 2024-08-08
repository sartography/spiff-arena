# Wish List

The following is a list of enhancements we wish to complete in the near (or even distant) future.

## Performance / System Improvements

### Benchmarking / Performance Testing

Automated tests that ensure our performance remains consistent as we add features and functionality.

### Support Multiple Connector Proxies

Service Tasks have been a huge win; there are multiple reasons why supporting more than one Connector Proxy would be beneficial:

1. Connect to several separately hosted services.
2. Support multiple services written in multiple languages.
3. Allow some connectors to be local (HTTP GET/POST) vs. remote (Xero/Coin Gecko).
4. Could support non-HTTP-based connectors (Git interactions could be a workflow).

### Interstitial Performance ✔️

Push all processing to the background so the interstitial is just querying, not running (new item).

### Authentication Keys ✔️

Provide the ability to access API endpoints using an access key or an authentication process that is specifically designed for API calls.
(We currently rely on grabbing the JSON token to do this, which is not a real solution.)

### Core BPMN Features

There are a number of useful BPMN components that we do not currently support.
We should evaluate these and determine which ones we should support and how we should support them.
We should consider creating a list of unsupported items.

- Compensation Events (valuable but difficult).
- Conditional events.
- Event Sub-Processes are not currently supported (low-hanging fruit, easy to add).

### Decentralized / Distributed Deployments

This is a broad topic and will be covered in a separate document.
But consider a SpiffWorkflow implementation that is deployed across a cluster of systems and manages transactions on a shared Blockchain implementation.
Such a structure could assure compliance with a set of blessed BPMN diagrams.
Such a system could support highly transparent and auditable processes that could drive a DAO-based organization.

### Improve Parallel Processing

We should support the parallel execution of tasks within a single process whenever possible.
This is not as far-fetched or difficult as it may initially seem.
While Python is notoriously bad at parallel execution (the lovely GIL), we have already taken the most critical steps to ensuring it is possible:

1. A team has demonstrated parallel execution using the core SpiffWorkflow library.
2. We can keep a configurable number of "background" SpiffArena processes running that can pick up waiting tasks.

Given these things are already in place, we just need to lock processes at the task or branch level so that ready tasks on parallel branches can be picked up by different background processes at the same time.

### BPMN Definitions at Save Time vs. Run Time

Improve performance by pre-processing the BPMN Specification and generating the internal JSON representation so we no longer incur the expense of doing this on a per-process basis.
This will also allow us to do some early and deep validation as well.

## End User Experience

### UI Overview

We could really use a good UI/UX review of the site and take a stab at cleaning up the whole site to follow some consistent design patterns and resolve potential issues.

### Customizable Home Page (Non-Status Specific) ✔️

Allow a way to define custom landing pages that create different experiences for different organizations/needs.

### Markdown Rendering Could Be Better

1. When creating a bulleted or numbered list, no bullets or numbers are displayed. This is a bug in our style sheets or something that is clearing out all styles.
2. Limit the width of paragraphs to something reasonable. Having a line of text stretch across the entire screen is not a good experience.
3. Add support for MyST. This provides a set of standard extensions to Markdown and is the extension we are using for our own documentation.
4. Add support for parsing and displaying task data/Jinja2 syntax so you can immediately see how you are formatting the task data. Provide an additional area for setting the task data and have it render that information in place.

## Administrator / Support Contact Information

Allow defining contact information at the process group and process model level, perhaps at some very top level as well, which can be inherited unless overridden.
This information could then be displayed when a process is in a non-functional state, such as an error, suspended, or terminated state.
It might also be available in the footer or under a help icon when displaying a process instance.

### Process Heatmap

Allow administrators to see an overlay of a BPMN diagram that shows all the process instances in the system and where they are (20 people are waiting on approval, 15 are in the re-review, etc.
).

## Modeler Experience

### DMN Editor Sucks

Can we build a better DMN editor?
Trisotech seems to do it very well.
I would love to have a day or two just to research this area and see if there is just another open-source project we can leverage, or if we could build our own tool.

### Modeler Checker

At runtime, or when you save, it would be great if we could execute a:

- Validation Report - what is wrong with the model? Is it valid BPMN? Are there intrinsic errors?
- Linting Report - Does the model follow common naming conventions, styles, are there deadlocks, etc.? Many of these tools already exist; we just need to integrate them!

### Plugins and Extensions

- Track down our previous research and add here. Color picker, etc.

### Automated Testing ✔️

Incorporate an end-to-end testing system that will allow you to quickly assure that a BPMN model is working as expected.
Imagine Cypress tests that you could define and execute in the modeler.

### JSON Schemas Everywhere!

Our forms are JSON Schemas (a description of the data structure).
We could do similar things for Service Tasks, Script Tasks, etc., such that the modeler is at all times aware of what data is available, making it possible to build and execute a task as it is created.

### Markdown Support for Process Groups and Models

Allow us to define a markdown file for a process group or process model, which would be displayed in the process group or process model in the tile view, or at the top of the details page when a group or model is selected.

### Adding a Unit Test from Within the Script Editor Would Be Nice

### Form Builder ✔️

1. Let's invest in a much better Form Builder experience so that it is trivial to build new forms or modify existing simple forms. We don't want to implement everything here, but a simple builder would be very useful.
2. RJSF says it supports markdown in the headers, but it doesn't work for us.

### Text Area / Markdown / Select List for Service Task Parameters

The text box for entering parameters for a service task is uncomfortable, verging on maddening when trying to enter long parameters.
It would also be wonderful to offer a selection list if we have a known set of options for a given parameter.

### Moving Models and Groups

Right now, we allow editing the display name of a model or group, but it does not change the name of the underlying directory, making it harder and harder over time to look at GitHub or the file system and find what you are seeing in the display.

### Fast Feedback on Errors with Python Expressions

We have in the past considered changing the way lots of expressions worked such that you would have to include an equals sign in the front in order for it to be evaluated as Python, like [this](https://docs.camunda.io/docs/components/concepts/expressions/#expressions-vs-static-values).
The [status quo is confusing](https://github.com/sartography/spiff-arena/issues/1075), but Elizabeth pointed out that requiring string parsing in order to decide how to evaluate something is not necessarily better.
If the BPMN editor was aware of the variables that existed within the workflow, defined by the JSON schemas of forms, messages, and service calls, or the variables that come out of script tasks, then we could immediately notify people of the issue while they are authoring the diagram rather than having to wait for a possible runtime error.
We could also change the error message on evaluation errors to include a reminder that quotes are needed around strings.

### Editable tables in User Tasks

Right now you can present data in a tabular format at the top of a human task via instructions, but you cannot provide a table where the data is editable.
This is something that Volker called out as a desirable feature.

### Provide a way for a process model to be available in the modeling environment but not the runtime environment

This is available via "start" permissions, but Volker was wondering if there should potentially be another more accessible way to allow this type of function.

### Comments function

In a generic workflow system like this, there are many reasons why one might want to add a comment to a process instance.
The process model author can easily build a user task with a form that allows for comments.
As such, having a separate system for comments would in some ways be redundant.
But a separate system for comments would also allow for adding comments at any time, not just when a user task is active.
Comments from people tend to be highly relevant for coworkers who need to interact with processes, such as with approvals.
These comments could be more easily presented in the UI associated with a process instance.
The approver will be looking for this type of information, so having a standard place to put it might be beneficial.
