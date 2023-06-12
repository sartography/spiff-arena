# Wish List

The follow is a list of enhancements we wish to do complete in the near (or even distant future)

## Performance Improvements

### BPMN Definitions at save time vs run time
Improve performance by pre-processing the BPMN Specification and generating the internal JSON representation so we no longer incur the expense of doing this on a per-process basis.
This will also allow us to do some early and deep validation as well.

## End User Experience

### Administrator / Support Contact Information
Allow defining contact information at the process group and process model level, perhaps at some very top level as well - which can be inherited unless overridden.  
This information could then be displayed when a process is in a non-functional state - such an error, suspended, or terminiated state.
It might also be available in the footer or under a help icon when displaying a process instance.

## Modeler Experience

### Markdown Support for Process Groups and Models
Allow us to define a markdown file for a process group or process model, which would be displayed in the process group or process model in the tile view, or at the top of the details page when a group or model is selected.

### Form Builder
Let's invest in a much better Form Builder experience, so that it is trivial to build new forms or modify existing forms.

## Connector Proxy

### Support Multiple Connector Proxies
Service Tasks have been a huge win, there are multiple reasons that supporting more than one Connector Proxy would be beneficial:

1. Connect to several separately hosted services
2. Support mulitple services written in multiple languages
3. Allow some connectors to be local (http get/post) vs remote (xero/coin gecko)
4. Could support non http based connectors (git interactions could be a workflow)

