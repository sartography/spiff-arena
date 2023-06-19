# Wish List

The follow is a list of enhancements we wish to do complete in the near (or even distant future)

## Performance Improvements

### BPMN Definitions at save time vs run time
Improve performance by pre-processing the BPMN Specification and generating the internal JSON representation so we no longer incur the expense of doing this on a per-process basis.
This will also allow us to do some early and deep validation as well.

## End User Experience

### Markdown rendering could be better
1. When creating a bulleted or numbered list, no bullets or numbers are displayed.  This is a bug in our style sheets - or something that is clearing out all styles.
2. Limit the width of paragraphs to something reasonable.  Having a line of text stretch across the entire screen is not a good experience.
3. Add support for MyST - this provides a set of standard extensions to Markdown and is the extension we are using for our own documentation.  
4. Add support for parsing and displaying task data / Jinja2 syntax - so you can immediately see how you are formatting the task data. Provide an additional area for setting the task data, and have it render that information in place.

## Administrator / Support Contact Information
Allow defining contact information at the process group and process model level, perhaps at some very top level as well - which can be inherited unless overridden.  
This information could then be displayed when a process is in a non-functional state - such an error, suspended, or terminiated state.
It might also be available in the footer or under a help icon when displaying a process instance.

## Modeler Experience

### Markdown Support for Process Groups and Models
Allow us to define a markdown file for a process group or process model, which would be displayed in the process group or process model in the tile view, or at the top of the details page when a group or model is selected.

### Form Builder
1. Let's invest in a much better Form Builder experience, so that it is trivial to build new forms or modify existing simple forms.  We don't want to implement everything here - but a simple builder would be very useful.
2. RJSF says it supports markdown in the headers, but it doesn't work fur us.

### Text Area / Markdown / Select list for Service Task Parameters
The text box for entering parameters for a service task is uncomfortable, to verging on maddening when trying to enter long parameters.  Would also be wonderful to offer a selection list if we have a known set of options for a given parameter. 

### Moving Models and Groups
Right now we allow editing the Display name of a model or group, but it does
not change the name of the underlying directory, making it harder and harder
over time to look at GitHub or the file system and find what you are seeing in the display.

## System Improvements

### Support Multiple Connector Proxies
Service Tasks have been a huge win, there are multiple reasons that supporting more than one Connector Proxy would be beneficial:

1. Connect to several separately hosted services
2. Support mulitple services written in multiple languages
3. Allow some connectors to be local (http get/post) vs remote (xero/coin gecko)
4. Could support non http based connectors (git interactions could be a workflow)

### Improve Parallel Processing

