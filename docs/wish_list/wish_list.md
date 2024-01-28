# Wish List

The follow is a list of enhancements we wish to do complete in the near (or even distant future)

## Performance / System Improvements

### Benchmarking / Performance Testing
Automated tests that assure our performance remains consistent as we add features and functionality.

### Support Multiple Connector Proxies
Service Tasks have been a huge win, there are multiple reasons that supporting more than one Connector Proxy would be beneficial:

1. Connect to several separately hosted services
2. Support multiple services written in multiple languages
3. Allow some connectors to be local (http get/post) vs remote (xero/coin gecko)
4. Could support non http based connectors (git interactions could be a workflow)

### Interstitial Performance
push all processing to background so interstitial is just querying, not running (new item)

### Authentication Keys 
Provide an ability to access API endpoints using an access key - or authentication process that is specifically designed for API calls.  (we currently rely on the grabbing the json token to do this, which is not a real solution)

### Core BPMN features
There are a number of useful BPMN components that we do not currently support.  We should evaluate these and determine which ones we should support and how we should support them.  We should consider creating a list of unsuported items.

* Compensation Events (valuable, but difficult)
* Conditional events.
* Event Sub-Processes are not currently supported (low-hanging fruit, easy to add)

### Decentralized / Distributed Deployments
This is a broad topic and will be covered in a separate document.  But consider a SpiffWorkflow implementation that is deployed across a cluster of systems - and manages transactions on a shared Block Chain implementation.  Such a structure could assure compliance to a set of blessed BPMN diagrams.  Such a system could support highly transparent and auditable processes that could drive a DAO based organization.


### Improve Parallel Processing
We should support the parallel execution of tasks within a single process whenever possible to do so.  This is not as far-fetched or difficult as it may initially seem.  While Python is notoriously bad at parallel execution (the lovely GIL) - we have already taken the most critical steps to assuring it is possible:
1. A team has demonstrated parallel execution using the cure SpiffWorkflow library.
2. We can keep a configurable number of "background" SpiffArena processes running that can pick up waiting tasks.  
Given these things are already in place, we just need to lock processes at the task or branch level - so that ready tasks on parallel branches can be picked up by different background processes at the same time.

### BPMN Definitions at save time vs run time
Improve performance by pre-processing the BPMN Specification and generating the internal JSON representation so we no longer incur the expense of doing this on a per-process basis.
This will also allow us to do some early and deep validation as well.

### BPMN model versioning
The model has version control functionality, and the active instances of the model are not affected by subsequent updates, preserving existing workflows.

## End User Experience

### UI Overview
We could really use a good UI / UX review of the site and take a stab at cleaning up the whole site to follow some consistent design patterns and resolve potential issues. 

### Customizable Home Page (non Status specific)
Allow some way to define custom landing pages that create different experiences for different organizations / needs.

### Markdown rendering could be better
1. When creating a bulleted or numbered list, no bullets or numbers are displayed.  This is a bug in our style sheets - or something that is clearing out all styles.
2. Limit the width of paragraphs to something reasonable.  Having a line of text stretch across the entire screen is not a good experience.
3. Add support for MyST - this provides a set of standard extensions to Markdown and is the extension we are using for our own documentation.  
4. Add support for parsing and displaying task data / Jinja2 syntax - so you can immediately see how you are formatting the task data. Provide an additional area for setting the task data, and have it render that information in place.

## Administrator / Support Contact Information
Allow defining contact information at the process group and process model level, perhaps at some very top level as well - which can be inherited unless overridden.  
This information could then be displayed when a process is in a non-functional state - such an error, suspended, or terminiated state.
It might also be available in the footer or under a help icon when displaying a process instance.

### Process Heatmap
Allow administrators to see an overlay of a BPMN diagram that shows all the process instances in the system and where they are (20 people are waiting on approval, 15 are in the re-review .....)

### Tasks Permission
Each task can be assigned to a responsible person for handling.

## Modeler Experience

### DMN Editor Sucks
Can we build a better DMN editor? Trisotech seems to do it very well.  Would love to have a day or two just to research this area and see if there is just another open source project we can leverage, or if we could build our own tool.

### Modeler Checker 
At run time, or when you save it would be great if we could execute a:
* Validation Report - what is wrong with the model?  Is it Valid BPMN?  Are there intrinsic errors?
* Linting Report!  Does the model follow common naming conventions, styles, are there dead-locks, etc.  Many of these tools already exist, we just need to integrate them!

### Plugins and Extensions 
* Track down our previous research and add here.  Color picker, etc....

### Automated Testing ✔️
Incorporate an end-to-end testing system that will allow you to quickly assure that
a bpmn model is working as expected.  Imagine Cypress tests that you could define and execute in the modeler.

### Json Schemas Everywhere!
Our forms are Json Schemas (a description of the data structure) - we could do similar things for Service Tasks, Script Tasks ... such that the modeler is at all times aware of what data is available - making it possible to build and execute a task as it is created.

### Markdown Support for Process Groups and Models
Allow us to define a markdown file for a process group or process model, which would be displayed in the process group or process model in the tile view, or at the top of the details page when a group or model is selected.

### Adding a unit test from within the script editor would be nice

### Form Builder
1. Let's invest in a much better Form Builder experience, so that it is trivial to build new forms or modify existing simple forms.  We don't want to implement everything here - but a simple builder would be very useful.
2. RJSF says it supports markdown in the headers, but it doesn't work fur us.

### Text Area / Markdown / Select list for Service Task Parameters
The text box for entering parameters for a service task is uncomfortable, to verging on maddening when trying to enter long parameters.  Would also be wonderful to offer a selection list if we have a known set of options for a given parameter. 

### Moving Models and Groups
Right now we allow editing the Display name of a model or group, but it does
not change the name of the underlying directory, making it harder and harder
over time to look at GitHub or the file system and find what you are seeing in the display.


