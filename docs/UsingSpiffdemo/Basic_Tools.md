# Building Blocks of the System
These process models serve as the foundational components of our 
system, forming the building blocks for creating powerful workflows. 

It is essential to gain a thorough understanding of each process model
on an individual level, comprehending their functionalities and
capabilities. 

Here are fundamental blocks of our system:

## Displaying Content
The Spiffarena platform offers powerful features for displaying content  within your BPMN processes.
Follow the steps below to effectively display content in your processes:

In this guide, we'll explore how to effectively display content in Spiffarena, providing a seamless user experience and engaging presentation of information. 

Let's dive in and learn the key aspects of displaying content within your workflows.

### Markdown: Formatting Content
Markdown is a powerful tool for formatting and styling your content in Spiffarena. With Markdown, you can easily add headings, lists, tables, hyperlinks, and more to enhance the readability and visual appeal of your displayed content. 

### Jinja Templating: Dynamic Content Generation

Jinja Templating in Spiffarena empowers you to generate dynamic 
content based on variables, conditions, and logic. By leveraging 
Jinja's syntax and functionality, you can customize your content to 
adapt to specific scenarios, display personalized information, or 
perform calculations based on collected data.

### Combining Markdown and Jinja: Unleashing the Power

By utilizing the strengths of Markdown and Jinja, you can create rich, 
interactive, and data-driven content that goes beyond static text.
We'll demonstrate using an example on how to leverage Markdown and Jinja together to create captivating content that responds to user input and presents  dynamic information.

### Basic Example for displaying content

In our Spiffarena dashboard, we have a simple example of how to display content in the basics section. Now, let's explore the process workflow of the content display process model and discover various ways to present content in different scenarios.

#### Display Content Process Overview:

![Image](Images/Display_Content.png)

Here is a summary of the process:

1. **Start Event and Introduction Manual Task**

![Image](Images/Introduction_manual.png)

The process begins with a Start Event, signaling the start of the 
workflow.

It is followed by a Manual Task called "Introduction" that displays a 
welcome message or instructions for the users. The content to be 
displayed is specified in the task's properties panel.

![Image](Images/Manu_instructions_panel.png)

2. **User Task with Form**

A User Task named "simple form" is included, allowing users to 
complete a form.
The properties panel of the User Task contains a JSON form schema, 
defining the structure of the form.
The instructions panel of the User Task guides users to fill out the 
form, indicating that the entered values will be shown in the 
subsequent Manual Task.

![Image](Images/User_instructions.png)

3. **Script Tasks**

Three Script Tasks are incorporated into the process, each serving a 
specific purpose.
Script Task 1 introduces a delay using the code "time.sleep(3)" and 
generates a dictionary of colors.
Script Task 2 includes a delay with the code "time.sleep(1)" and 
focuses on making the colors more playful.
Script Task 3 includes a delay with the code "time.sleep(2)" and aims 
to increase the silliness level.

![Image](Images/Script_instructions.png)

4. **Manual Task to Display Content**

![Image](Images/Manual_instructions.png)

A Manual Task will display content based on the collected data 
and script-generated information. The instructions panel of the Manual Task provides the content to be displayed, which includes the form data entered by the user.
It also offers an optional Chuck Norris joke based on user preference and a table of silly color names generated using Jinja templating.

![Image](Images/Manual_instructionss.png)

5. **End Event**

![Image](Images/End.png)

The process concludes with an End Event, indicating the end of the workflow.
The instructions panel of the End Event suggests next steps, such as exploring the diagram in edit mode and completing the "Request a Playground" task.

![Image](Images/end_message.png)

## Using Forms

This feature allows you to create custom forms for collecting and managing data within your workflows. Whether you need a simple feedback form or a complex multi-step form, Spiffarena provides you with the tools to build and integrate forms seamlessly.

With Spiffarena's form builder, you can start with basic form elements and gradually add more advanced components as your form requirements evolve. 
Let's dive in and explore the possibilities of creating forms in Spiffarena.

### Instructions on Creating Forms

Forms play a crucial role in capturing data, and Spiffarena offers a powerful form-building capability. Here are the ways to create forms:

1. Leveraging JSON Schema

JSON Schema is an emerging standard for describing the structure of data in a JSON file. JSON Schema forms the foundation for building forms in Spiffarena.

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


### Basic Example for Using Forms
Now that you have a grasp of how to create forms in Spiffarena using 
JSON Schema and RJSF, it's time to put your knowledge into action. 
Lets cover the example of using forms process model in the basics.

The BPMN diagram initiates with a start event, which is followed by a manual task aimed at providing a comprehensive understanding of web forms and the various approaches to displaying them. 
![Image](Images/Form_manual_editor.png)

The expected output of the form during the process execution can be observed in the attached image.

![Image](Images/manual_outpul.png)

Moving forward, the diagram incorporates a user task specifically designed for form display. Within the properties panel of the user task, two essential files are included: a JSON Schema (containing the form description in RSJF format) and a UI Schema (outlining the rules for displaying the form based on the RSJF schema). 

![Image](Images/BPMN_Form_display.png)

The anticipated output of the form when the process is executed can be visualized in the attached image.
![Image](Images/Form_display.png)


Following that, a manual task is included, offering a simple form explanation. As users submit the form, the manual task will display the respective explanation.
![Image](Images/Manual_lasttt.png)

An attached image provides an overview of the expected form output during the process execution.

![Image](Images/Manual_last.png)


## Writing Scripts 


asdas
## Making Decisions

asda
## Assigning Tasks

asda
## Gathering Information
asdads