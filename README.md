
![Tests](https://github.com/sartography/bpmn-js-spiffworkflow/actions/workflows/tests.yml/badge.svg?branch=main)

# SpiffWorkflow Extensions for BPMN.js
This package provides extensions that can be applied to BPMN.js that will enable some important features of [SpiffWorkflow](https://github.com/sartography/SpiffWorkflow) - the Python BPMN Library for executing business processes.  See below for more information.

**IMPORTANT**:  This is a work in progress, and is not yet released.

# About

This extension creates a BPMN editor with all the capabilities of [BPMN.js](https://github.com/bpmn-io/bpmn-js) and the following additions / modifications:

* Ability to insert BPMN's Data Input and Data Output Objects.
* A SpiffWorkflow centric Properties Panel for specifying scripts to run before and after a task, and for defining documentation, and Mark-up content for displaying in user and manual tasks.  Among other things.

# Future Plans
* We look forward to integrating a real time Python execution environment for live script development.

# Data Input and Data Output Element
This extension will allow you to drag BPMN Data Input and Data Output elements onto the diagram and give them appropriate labels.  This will generate valid BPMN elements in the underlying XML file - connecting them to the IO Specification of the process, as shown below:
```xml
  <bpmn:process id="my_delightful_process" isExecutable="true">
    <bpmn:ioSpecification>
      <bpmn:dataInput id="DataInput-745019423-1" name="num_dogs" />
      <bpmn:dataOutput id="DataOutput-711207596-1" name="happy_index" />
    </bpmn:ioSpecification>
    ...
```
![Screenshot](docs/io.png)

Using these data input and outputs will allow you to create processes designed to be used as Call Activities.  SpiffWorkflow (in a soon-to-be released version) will pick up this information, and enforce it.  So that you must provide these input variables to execute, and only the variables mentioned in the output will be passed back to the calling process.

## Usage
```javascript
import BpmnModeler from 'bpmn-js/lib/Modeler';
import spiffworkflow from 'bpmn-js-spiffworkflow/app/spiffworkflow';


var bpmnJS = new BpmnModeler({
  additionalModules: [
    spiffworkflow
  ],
  moddleExtensions: {
    spiffworkflowModdle: spiffModdleExtension
  }
});
```

## Run the Example

You need a [NodeJS](http://nodejs.org) development stack with [npm](https://npmjs.org) installed to build the project.

To install all project dependencies execute

```sh
npm install
```

To start the example execute

```sh
npm start
```

To build the example into the `public` folder execute

```sh
npm run all
```

## License
MIT
