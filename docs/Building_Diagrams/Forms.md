# Using Forms

This feature allows you to create custom forms for collecting and 
managing data within your workflows. Whether you need a simple 
feedback form or a complex multi-step form, SpiffArena provides you 
with the tools to build and integrate forms seamlessly.

With SpiffArena's form builder, you can start with basic form elements 
and gradually add more advanced components as your form requirements 
evolve. 
Let's dive in and explore the possibilities of creating forms in 
SpiffArena.

## Instructions on Creating Forms

Forms play a crucial role in capturing data, and SpiffArena offers a 
powerful form-building capability. Here are the ways to create forms:

1. Leveraging JSON Schema

JSON Schema is an emerging standard for describing the structure of 
data in a JSON file. JSON Schema forms the foundation for building 
forms in SpiffArena.

To simplify the form creation process, we leverage the React JSON 
Schema Form (RJSF) library. RJSF is a powerful tool that uses JSON 
Schema as its basis. It enables you to create dynamic and interactive 
forms with ease. The RJSF library is open source, free to use, and 
follows the principles of open standards.

![Image](Images/Form_json.png)

Please note that while this guide provides a basic understanding of 
JSON Schema and RJSF, there is much more to explore. We encourage you 
to refer to the official [RJSF documentation](https://rjsf-team.github.
io/react-jsonschema-form/docs/) for comprehensive details 
and advanced techniques.

2. Using Form Builder

An alternative approach to creating JSON code is to utilize the form 
builder feature, which allows you to easily create various fields 
without the need for writing JSON manually. 

However, it's important to 
note that the form builder may have certain limitations in terms of 
features and may not be as powerful as using the JSON editor directly. 

While the form builder provides convenience and simplicity, using the 
JSON editor offers greater flexibility and control over the form 
structure.

![Image](Images/Form-Builder.png)


## Basic Example for Using Forms
Now that you have a grasp of how to create forms in SpiffArena using 
JSON Schema and RJSF, it's time to put your knowledge into action. 
Lets cover the example of using forms process model in the basics.

The BPMN diagram initiates with a start event, which is followed by a 
manual task aimed at providing a comprehensive understanding of web 
forms and the various approaches to displaying them. 
![Image](Images/Form_manual_editor.png)

The expected output of the form during the process execution can be 
observed in the attached image.

![Image](Images/manual_outpul.png)

Moving forward, the diagram incorporates a user task specifically 
designed for form display. Within the properties panel of the user 
task, two essential files are included: a JSON Schema (containing the 
form description in RSJF format) and a UI Schema (outlining the rules 
for displaying the form based on the RSJF schema). 

![Image](Images/BPMN_Form_display.png)

The anticipated output of the form when the process is executed can be 
visualized in the attached image.
![Image](Images/Form_display.png)


Following that, a manual task is included, offering a simple form 
explanation. As users submit the form, the manual task will display 
the respective explanation.
![Image](Images/Manual_lasttt.png)

An attached image provides an overview of the expected form output 
during the process execution.

![Image](Images/Manual_last.png)