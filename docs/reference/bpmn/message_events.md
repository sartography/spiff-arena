# Message Events

Message Events send or receive information between process participants. They are not email
operations: use a connector if the process needs to send an email.

For a complete authoring walkthrough, see
[Send and Receive Messages Between Processes](/how_to_guides/building_diagrams/send_and_receive_messages).

![Message relationships](/images/relationship_message.png)

## Start Message Event

![Message Start Event symbol](/images/start_message_event_1.png)

![Process started by a message](/images/msg_event_example_3.png)

A Message Start Event starts a new process instance when a message is received.
Use **Variable Name** to specify where the received payload is stored.

## Intermediate Message Throw Event

![Intermediate Message Throw Event symbol](/images/intermediate_throw_msg_event.png)

![Message exchange between participants](/images/msg_event_example_2.png)

An Intermediate Message Throw Event sends a message and continues execution.
Its **Payload** expression supplies the message body. It does not wait for a response.

## Intermediate Message Catch Event

![Intermediate Message Catch Event symbol](/images/intermediate_catch_msg_event.png)

![Message exchange across separate diagrams](/images/msg_event_example_5.png)

An Intermediate Message Catch Event waits for a message before continuing.
Use matching conditions to route a message to the intended waiting instance when multiple
instances can receive the same message name.

## End Message Event

![End Message Event symbol](/images/end_msg_event.png)

![Message sent at the end of a process](/images/msg_event_example_4.png)

An End Message Event sends a message when that execution path ends. Other active paths
in the process are not necessarily finished.

## Correlation

Correlation associates a message with a process instance. Unlike a broadcast signal,
a message is intended for a particular receiver.

A message's correlation property has an identifier and a **Retrieval Expression** that extracts
a value from the message body. A receiving element's **Matching Conditions** supply expressions
for the expected values from task data. These are separate from **Variable Name**, which determines
where the received body is stored.

A property name does not implicitly select a task-data variable. Earlier messages may establish
correlation values; without saved values, a receiver may match by message name alone.
See the [matching example](/how_to_guides/building_diagrams/send_and_receive_messages)
for explicit configuration and type-matching pitfalls.

## Message Event Configuration

The current Arena properties panel exposes a **Message** section on message-capable elements:

| Field or control | Applies to | Purpose |
| --- | --- | --- |
| Which message is this associated with? | Senders and receivers | Select the message definition. |
| Message editor button | Senders and receivers | Open Message Editor to manage the definition and correlation properties. |
| Payload | Senders | Expression providing the outgoing message body. |
| Variable Name | Receivers | Task-data variable receiving the message body. |
| Enable Condition Matching | Receivers | Show the matching-condition fields. |
| Matching Conditions | Receivers with condition matching enabled | Expressions for expected correlation values, labeled by property identifier. |

**Message Editor** provides **Use Existing Shared Message**, **Location**, **Message Name**,
**JSON Schema**, and **Correlation Properties** (Property Name and Retrieval Expression).
Location identifies the existing process group that owns the shared definition. Definitions are
available to that group and descendants, with the nearest definition taking precedence.

BPMN files still contain embedded message and
correlation definitions; after shared definitions change, synchronize with **Update diagram**
and save each affected diagram.

## Related guides

- [Send and Receive Messages Between Processes](/how_to_guides/building_diagrams/send_and_receive_messages)
- [Message Tasks vs. Message Events](message_events_vs_tasks)
- [Messages API](/reference/api/messages)
