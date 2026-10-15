# Message Tasks vs. Message Events

Both tasks and events can send or receive messages. Choose the BPMN element that expresses
its role in the process; neither choice automatically implements a request-and-response exchange.

| Element | Behavior |
| --- | --- |
| Send Task | Sends a message as an explicit activity, then continues. Does not wait for a reply. |
| Receive Task | Waits for a message as an explicit activity before continuing. |
| Intermediate Message Throw Event | Sends a message at a point in the flow, then continues. |
| Intermediate Message Catch Event | Waits for a message at a point in the flow. |
| Message Start Event | Starts a process instance on receipt of a message. |
| Message End Event | Sends a message as an execution path ends. |
| Boundary Message Event | Reacts to a message while its attached activity is active; interrupting behavior depends on the boundary event configuration. |

For example, model **Notify Chef** as a Send Task and **Wait for Meal** as a Receive Task or
Intermediate Message Catch Event. The send alone does not wait for the meal. A Message Start
Event can start the Chef's process when the order arrives.

Sending is not the same as interrupting: throwing events send messages, while catching events
receive them. Not every Message Event interrupts a process or activity.

## Related guides

- [Send and Receive Messages Between Processes](/how_to_guides/building_diagrams/send_and_receive_messages): shared definitions, payloads, and matching replies.
- [Message Events](message_events): event types and current properties-panel fields.
