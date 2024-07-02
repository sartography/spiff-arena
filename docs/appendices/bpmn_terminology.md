# BPMN Terminology

## Activity

This refers to the work carried out by an individual or an organization within a process.
Activities can be classified into three categories: Task, Subprocess, and Call Activity.
These activities can be either atomic or non-atomic.
Atomic activities are indivisible and represent single tasks, while non-atomic activities involve multiple steps or subprocesses that work together to achieve a larger objective.

## Boundary Event

This refers to an event that can be triggered while an activity is in progress.
Boundary events are utilized for error and exception handling purposes.

## BPMN Model

This is a visual depiction of a business process designed to be both human-readable and machine-readable, typically represented in XML format.

## Business Process

This is a sequence of interconnected activities conducted by individuals and systems, following a defined order, with the aim of delivering a service or product, or accomplishing a specific business objective.
These processes involve the receipt, processing, and transfer of information and resources to generate desired outputs.

## Diagram

This is the visual platform where business processes are represented and mapped out.

## Call Activity

This refers to the act of a parent or higher-level process invoking a predefined or reusable child process, which is represented in another process diagram.
This invocation allows for the utilization of the child process multiple times, enhancing reusability within the overall model.

## Collapsed Subprocess

This is a Subprocess that conceals the underlying process it includes.

## Connecting Element

These are lines that establish connections between Flow Elements within a process, creating a Flow.
There are four distinct types of connecting elements: Sequence Flows, Message Flows, Associations, and Data Associations.

## Elements

These are the fundamental components used to construct processes.
These elements encompass Flow Elements, Connecting Elements, Data Elements, Artifacts, and Swimlanes.

## End Event

This marks the conclusion of a process.
An End Event can result in a Message, Error, or Signal outcome.

## Error

This denotes a significant issue encountered during the execution of an Activity or process, indicating a failure or malfunction in the processing.

## Event

This is an occurrence within a process that influences the Flow and typically involves a trigger and/or a result.
Events can be categorized into four types: Start, Intermediate, End, and Boundary.

## Event-Based Gateway

This marks a specific point within the process where alternative paths are initiated based on the occurrence of an Event.

## Exception

This is an Event within the process that deviates from the normal flow of execution.
Exceptions can be triggered by Time, Error, or Message Events.

## Exclusive Gateway

This denotes a juncture within the process where multiple alternative paths are available, but only one path can be chosen.
The decision regarding the chosen path is determined by a condition.

## Expanded Subprocess

This is a Subprocess that shows the process it contains.

## Gateway

This is a component that governs the available paths within a process.
Gateways can merge or diverge paths or introduce additional paths based on conditions or Events.
There are four types of Gateways: Exclusive, Parallel, Inclusive, and Event-Based.

## Intermediate Event

This is an event that occurs in the middle of a process, neither at the start nor the end.
It can be connected to other tasks through connectors or placed on the border of a task.
It evaluates conditions and circumstances, triggering events and enabling the initiation of alternative paths within the process.

## Join

This refers to the process of merging two or more parallel Sequence Flows into a single path using a Parallel Gateway.

## Lane

These are subdivisions within a Pool that are utilized to assign activities to specific roles, systems, or departments.

## Merge

This is the process in which two or more parallel Sequence Flow paths converge into a single path, achieved either through multiple incoming Sequence Flows or by utilizing an Exclusive Gateway.
This merging of paths is also commonly referred to as an "OR-Join."

## Message

This signifies the content of a communication exchanged between two Participants.
The message is transmitted through a Message Flow.

## Non-atomic Activity

This refers to an Activity that can be further decomposed into more detailed steps or subtasks.
A Subprocess is an example of a non-atomic Activity.
It is also commonly referred to as a "compound" Activity.

## Parallel Gateway

This indicates a specific point within the process where the Flow divides or merges into multiple parallel paths.

## Parent Process

This is a process that contains a Subprocess.

## Participant

This refers to a business entity, which can be an organization, department, unit, or role involved in a process.

## Pool

This represents a Participant in a process.

## Sequence Flow

This specifies the sequence and behavior of the Flow Elements within a process.

## Signal

This is an Event that is transmitted to all individuals or entities participating in a process.

## Start Event

This indicates where a process starts.

## Subprocess

This is a self-contained and compound Activity incorporated within a process, capable of being further decomposed into smaller units of work.

## Swimlane

This is a visual representation that separates processes based on the Participants responsible for performing them.
Swimlanes are comprised of Pools and Lanes.

## Task

This is an action performed by a person, an application, or both.

## Text Annotation

This provides additional information about the elements in a diagram.

## Trigger

This is a mechanism that detects and identifies a particular condition or circumstance within a Start Event or Intermediate Event, subsequently initiating a corresponding response.
