# connector-proxy-demo
A Spiff-Connector for demonstration purposes - shows how to build connectors to some common 3rd party systems. 

# How to create a Connector Proxy for SpiffWorklow

## Step 1. Create a python project with a few dependencies:
Create a bare-bones Flask application that depends on the core spiffworkflow-proxy (a flask blueprint)
and any connector dependencies you wish to use.
We will hopefully be adding a number of available connectors in the future.  Please checkout the connector-aws repository for an example of how to create connections to new services.  
``` python
  python = "^3.11"
  Flask = "^2.2.2"
  spiffworkflow-proxy = {git = "https://github.com/sartography/spiffworkflow-proxy"}
  connector-aws = { git = "https://github.com/sartography/connector-aws.git"}
```

## Step 2.
Create a basic Flask Application that uses the SpiffWorkflow Proxy's Flask Blueprint
```python
import os
from spiffworkflow_proxy.blueprint import proxy_blueprint
from flask import Flask

app = Flask(__name__)
app.config.from_pyfile("config.py", silent=True)
app.register_blueprint(proxy_blueprint)
if __name__ == "__main__":
    app.run(host="localhost", port=5000)
```

## Step 3.
Fire it up.  
```bash
#> flask run
```

## Optional API key protection

Set `SPIFF_CONNECTOR_PROXY_API_KEY` on this connector proxy to require callers to
send the `Spiff-Connector-Proxy-Api-Key` header.

When Spiff Arena is the caller, set the backend's
`SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_API_KEY` to the same value. Arena will add
that value to connector proxy requests for command discovery, authentication
metadata, and service task execution.

Any dependencies you add will now be available for SpiffWorkflow to call using a Service Task.  What's more, those services are now discoverable!  So when someone drops a Service Task into their diagram, they will have a dropdown list of all the services you have made available to them.  And those services will know what parameters are required, and can prompt diagram authors to provide information necessary to make the call.  Which can be no parameters at all (Just give me a fact about Chuck Norris) ... to complex parameters (a json structure to be added to a DynamoDB Table).

