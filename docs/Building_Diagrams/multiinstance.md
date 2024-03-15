# Multi-instance Tasks
Multi-instance tasks in BPMN (Business Process Model and Notation) represent a powerful construct for modeling processes that require repetitive actions over a collection of items. 

These tasks automate the iteration over a list, array, or collection, executing the specified activity for each element within. Multi-instance tasks can be configured to run either in parallel, where all instances are executed simultaneously, or sequentially, where each instance is executed one after the other.

## **Sequential Execution**

Tasks are executed one after another, ensuring that each task instance begins only after the previous one has completed.
In case of a sequential multi-instance activity, the instances are executed one at a time. When one instance is completed, a new instance is created for the next element in the inputCollection.

![Multi_instance_Sequential](images/multiinstance_sequential_example.png)

## **Parallel Execution**

All instances of the task are launched simultaneously, allowing for concurrent processing of the collection elements. In case of a parallel multi-instance activity, all instances are created when the multi-instance body is activated. The instances are executed concurrently and independently from each other.

![Multi_instance_parallel](images/multiinstance_parallel_example.png)

## Components of Multi-Instance Tasks
Multi-instance tasks comprise several key properties that define their behavior:

```{image} ./images/multiinstance_properties.png
:width: 230px
:align: right 
``` 
1. **Input Collection**: Specifies the array or collection over which the task iterates. Each element in the collection serves as input for a task instance.


2. **Output Collection**: Collects the outcomes from all task instances into a single collection, enabling aggregation of results. Do not use this property when Loop Cardinality is specified.

3. **Loop Cardinality**: Defines the exact number of times the task should iterate. This is used when the number of instances is known ahead of time and is fixed. Do not use this property when Output Collection is specified.

4. **Input Element Variable**: Represents each element in the input collection during an iteration, allowing for individual processing.

5. **Output Element Variable**: Captures the result of each task instance, contributing to the output collection.

6. **Completion Condition**: An optional condition that, when evaluated as true, can prematurely terminate the iterations.


## Example: Using Multi-Instance Tasks for Dynamic Iteration

This example outlines a BPMN process that demonstrates the use of a multi-instance task to iterate over and modify elements within a collection. 

Specifically, the process manages a list of composers, their names, and genres, showcasing the dynamic handling of data through script and manual tasks.

### Process Overview:

#### 1. **Start Event**: 

Marks the initiation of the process.

![Multi_instance_example](images/multiinstance_example1.png)

#### 2. **Script Task - Create Dictionary**:


This task initializes a list (array) of dictionaries, each representing a composer with their name and associated genre. The script effectively sets up the data structure that will be manipulated in subsequent steps of the process.

![Multi_instance_example](images/multiinstance_example2.png)

**Script**:

```python
    composers = [
       {"composer": "Johann Sebastian Bach", "genre": "Baroque"},
       {"composer": "Ludwig van Beethoven", "genre": "Classical/Romantic"},
       {"composer": "Wolfgang Amadeus Mozart", "genre": "Classical"}
     ]
```

#### 3. **Multi-Instance Task - Edit Composer**:

This task is configured as a parallel multi-instance task that iterates over the `composers` array created by the previous script task. It allows for the editing of each composer's information within the array.

![Multi_instance_example](images/multiinstance_example3.png)

**Properties Configuration**:

- **Input Collection**: The `composers` array to iterate over.
- **Input Element**: Each element in the collection is referenced as `c` during the iteration.
- **Output Collection**: The modified `composers` array, reflecting any changes made during the iteration.
- **Form Attachment**: A web form defined by `composer-schema.json` is attached to facilitate the editing of composer details within the web interface.

```{admonition} Note
⚠ The completion condition and output element are left unspecified, indicating that the task completes after iterating over all elements in the input collection without additional conditions.
```

#### 4. **Manual Task - Display Edited Composers**:

This task presents the edited list of composers and their genres, using a loop to display each composer's name and genre in the format provided.

![Multi_instance_example](images/multiinstance_example4.png)

**Instructions**:

```python
     {% for c in composers %}
     * **{{c.composer}}**:   {{c.genre}}
     {% endfor %}
```

This templating syntax iterates over the `composers` array, displaying each composer's name and genre in a formatted list.

5. **End Event**:

Signifies the successful completion of the process instance, after the list of composers has been edited and displayed.

### Summary:

This multi-instance example in a BPMN process highlights the capability to dynamically handle collections of data through scripting and manual tasks. By iterating over a list of composers, allowing for the editing of each item, and finally displaying the edited list, the process demonstrates how data can be manipulated and presented in a structured workflow, showcasing the flexibility and power of BPMN for data-driven processes.
