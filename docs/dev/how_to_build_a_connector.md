# How to build a connector

While existing connectors like connector-http are very flexible, you may choose to build a connector for a specific use case.

To get an idea of what you are in for, take a look at existing connectors:

* [connector-http](https://github.com/sartography/connector-http/blob/main/src/connector_http/commands/get_request_v2.py)
* [connector-smtp](https://github.com/sartography/connector-smtp/blob/main/src/connector_smtp/commands/send_email.py)

And there are [many more connectors](https://github.com/sartography?q=connector&type=public&language=python&sort=).

A connector can implement many commands.
Commands are also known as operators in the SpiffWorkflow frontend properties panel user interface.
Like the above examples, you will want to inherit from the `ConnectorCommand` class.
You will see that there are two important functions that your command class must implement:

* `__init__`
* `run`

Code introspection is used based on the implementation of the `__init__` method to determine which parameters should be allowed in the properties panel.
The `run` method is where the actual work is done (send HTTP request, etc).

If you end up writing a connector, please consider contributing it back to the community and please consider contributing to this documentation.
Thank you!
