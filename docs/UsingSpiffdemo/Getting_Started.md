# Using Spiffdemo.org
Spiffdemo is a demo version of Spiffworkflow, offering a limited set of functions and features. It provides users a platform to explore workflow concepts through a collection of top-level examples, diagrams, and workflows. Users can interact with pre-built models, make modifications, and visualize process flows.
Spiffdemo serves as a demonstration version of Spiffworkflow, providing a glimpse into its capabilities with limited functionality. Spiffworkflow, on the other hand, is a full-fledged tool that offers a broader range of features for creating and managing workflows.

| Category        | Spiffdemo (Demo Version) | SpiffWorkflow (Full Version) |
|---------|-------------------------|------------------------------|
| Functionality | Limited set of functions and features | Comprehensive set of features and functions for creating, managing, and optimizing process models and workflows |
| Purpose | Provides a platform for exploration and demonstration of workflow concepts | Enables users to create, manage, and optimize their own process models and workflows for their specific needs and requirements |
| Features | Limited functionality for interacting with pre-built models and making modifications | Advanced features such as task management, process modeling, diagram editing, and customizable properties |

## How to Login to Spiffdemo
To begin your journey with Spiffdemo, open your web browser and navigate to the official Spiffdemo website. 
On the login screen, you will find the option to log in using Single Sign-On. Click the Single Sign-On button and select your preferred login method, such as using your Gmail account.

<p align="center">
<img src="https://lh3.googleusercontent.com/lfwuApYvOV1336IIbaQnh63niw6mmLJkpyFjM6lm3oHXClzwSh9O7l4q6CGmIjLrTRrHd_DzRGP7E-Km7IcD-zg0PZmw2IpTLjzQgTCiJSASZqFplvhHCfmXMvHcKDotNAYwRIcAEWYSrlLuka4U8Nk" alt="drawing" width="400"/>


```{admonition} Note: Stay tuned as we expand our sign-on options beyond Gmail. More ways to access Spiffdemo are coming your way!
```
## Exploring the Examples

When logging into the dashboard, it is crucial to familiarize yourself with the functions it offers and how the underlying engine operates. In the demo website, we will explore two examples: the Minimal Example and the Essential Example, to provide a clear understanding of the process.


![](https://lh5.googleusercontent.com/Db25xtzQon8tu4YbsOLx-DPEyONhrF5jfxhbEXOqDomT2YlGnhEWBZMVFF84ViPyCRD-HMca--Xl4bj8vIF5-KNfpoKjujUZk1wDIMuBMymbg0o1jgucPrZxSsxxT1GuLYGjXPwCyEQ8BhpSt6URJCg)

  

###  Minimal Example

Let's begin with the Minimal Example, which serves as a "Hello World" process—a simple executable BPMN Diagram designed to demonstrate basic functionality. Rather than immediately starting the process, we will first examine its structure.

![](https://lh3.googleusercontent.com/MBj52gja_U5V4R7AQ1yMTwG3GoexCPLG-7Xwe40xURIOUYqJhGmQRapPln37QM9ylLiy17Oq0B1BHvsRQWVpAzd9ztt2AUs9XG26HUOORNXpgJNOGEt4DXG-_wh6YK7X4ms52W2O5yzOgdlIJ48dMOA)

#### Access the Process Directory

Clicking on the process name will open the directory dedicated to the Minimal Example process. From here, you can start the process if desired, but for the purpose of this example, we will proceed with an explanation of its components and functionality. Therefore, Locate and click on the .bpmn file to access the BPMN editor.

  

![](https://lh3.googleusercontent.com/EKwOS_K29tFCDvIpdZHI2Ca_ZA8H5fw127OkUL3aAHw-JRjnDqsemFUyLXAKxr2CnsUfuAiY3yPswM03O04O57belSJnEi2PPeAfVElU-mraD3XV0v0ggQJsAuvdaMBf2-eOGsOIS5CCBp9et3IxR70)

  

The BPMN editor provides a visual representation of the process workflow.

  

![](https://lh4.googleusercontent.com/kvDwQPz65ABWc653Ou54r9yfwGc1RHlzufKOE4oQ0uKsM_CRnuQPObAkbh9ldoXHUkGODZrLcdInKXMGOFra0wKoPxtvsdEASORHnuSTayOe_MEChuEqymJ5ur6rcuoCMQXKH7f-dfPAEBg2vukT53w)

  

#### Understand the Process Workflow

  

The Minimal Example process consists of three key elements: a start event, a manual task, and an end event. It is essential to understand the purpose and functionality of the properties panel, which is an integral component of the process diagram. Without selecting any specific task within the diagram editor, the properties panel will appear as follows:

![](https://lh4.googleusercontent.com/Yx4xI4TmhLzdGfV68nKpamfgSZMDnK4d9-FKh99SEZjqmIXjl8coxbaWU9OACHszx6AiKUKIL21OKiiW-tZ9iyxMVJGE6yx8JTg8eEnthcp1h8Z3GugkvUdwlwax9aJtKW6DYBQBhHxXeVplWoazSKg)

General

-   Name field is usually empty unless user wants to provide it. It serves as a label or identifier for the process.
    
-   The ID is automatically populated by the system (default behavior) however it can be updated by the user, but it must remain unique within the other processes.
    
-   By default, all processes are executable, which means the engine can run the process.
    

Documentation

-   This field can be used to provide any notes related to the process.
    

Data Objects

-   Used to configure Data Objects added to the process. See full article [here](https://medium.com/@danfunk/understanding-bpmns-data-objects-with-spiffworkflow-26e195e23398).
    

  
**1. Start Event**
    

The first event in the minimal example is the start event. Each process diagram begins with a Start Event. Now explore the properties panel when you click on the first process of the diagram, “Start Event”.

![](https://lh6.googleusercontent.com/-lXbK5RuTDTykc-JBRd7eCbrrGHroB5gsl77UXU7IxEsw4nSPcMmxe3wRVTr242ZRORBlEdtrFZZhBQAyILOYTWv7-fsMSzMYD2jBqJx71lkxuaP9mnePJtY21qx7DA6XgELmmZl6uDIhFwHcEaPYqM)

General

-   The Name for a Start Event is often left blank unless it needs to be named to provide more clarity on the flow or to be able to view this name in Process Instance logs.
    
-   ID is automatically populated by the system (default behavior) however it can be updated by the user, but it must remain unique within the process. Often the ID would be updated to allow easier referencing in messages and also Logs as long as it’s unique in the process.
    

Documentation

-   This field is used to provide any notes related to the element.
    

  ```{admonition} Note: In the minimal example, the Start Event is a None Start Event. This type of Start Event signifies that the process can be initiated without any triggering message or timer event. It is worth noting that there are other types of Start Events available, such as Message Start Events and Timer Start Events. These advanced Start Events will be discussed in detail in the subsequent sections, providing further insights into their specific use cases and functionalities.
```


**2. Manual Task**

Within the process flow, the next step is a manual task. A Manual Task is another type of BPMN Task requiring human involvement. Manual Tasks do not require user input other than clicking a button to acknowledge the completion of a task that usually occurs outside of the process.

Now explore the properties panel when you click on the first process of the process of “Show Example Manual Task”.  
![](https://lh6.googleusercontent.com/xbF6rEcK-agPjIl5bAMelArlnIpdgvMNCG-MB24130ZEm_pem8RpkZIn7Ej-cZ0uuBgW9ajGDFxbrEP7GDNnR4VUPrNcpTVyjMwxQUsKVB5lxzBsvVVWiDcbGGO5GtnqcqNTUasHgEwj-vunPmEz19M)

Panel General Section

-   Enter/Edit the User Task name in this section. Alternatively, double-click on the User Task in the diagram.
    
-   The ID is automatically entered and can be edited for improved referencing in error messages, but it must be unique within the process.
    

Documentation Section

-   This field is used to provide any notes related to the element.
    

SpiffWorkflow Scripts

-   Pre-Script: Updates Task Data using Python prior to execution of the Activity.
    
-   Post-Script: Updates Task Data using Python immediately after execution of the Activity.
    

Instructions

During the execution of this task, the following instructions will be displayed to the end user. This section serves as a means to format and present information to the user. The formatting is achieved through a combination of Markdown and Jinja. To view and edit the instructions, click on the editor, and a window will open displaying the instructions in the specified format.

![](https://lh4.googleusercontent.com/wWNqTB2EU4W0Hgz_u2l7PiEqbGVRuZMjtbgGUrckAPP9aD2TRGFvZgVkRXWcx-CV5JsSzWYDsZuXCkTpvmyfdUmFm13bTZ5o5OOf7ykBMoJ-vGBPcxQojSpE9leMn97zZDbEdJmZPgnrChQk6tbjUc8)


3.  ##### End Task
    

The next process in the workflow is an end task. A BPMN diagram should contain an end event for every distinct end state of a process.

Now explore the properties panel when you click on the last end event process:

![](https://lh5.googleusercontent.com/uu9dUBMExx7JxrVOtorZtc5doHlodI-dcvlWjO2L_qFz5-v9eN6vnIMLJC76Cb7PuabLjzR86EESP_Em7FTPEZssxS6ql-Prjmg-bK9MfaMAo5yyuUQ4IXsjhkFH60QEOjMY3r665LSL-R-pZAwyDg4)

General

-   The Name for a Start Event is often left blank unless it needs to be named to provide more clarity on the flow or to be able to view this name in Process Instance logs.
    
-   ID is automatically populated by the system (default behavior) however the user can update it, but it must remain unique within the process.
    

Documentation

-   This field is used to provide any notes related to the element.
    

Instructions

-   These are the Instructions for the End User, which will be displayed when this task is executed.You can click on launch editor to see the markdown file.
    

![](https://lh5.googleusercontent.com/lcGDq-colYTa0zRq5yObuN6D5aW2wH-PheyYFMPJ9D77lZ_-fQlUrtFHNwKmCod4v1JYrWnblJEzW5VkVFM_I_Q1d8fhiWC98DPK4ZDctI7Jbqf11DdXSJAUVvZ2C2ubv-3FKXzVkbgGY8Fnk0irSdo)