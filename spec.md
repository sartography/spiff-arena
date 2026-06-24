we recently merged https://github.com/sartography/spiffworkflow-proxy/pull/8, which was:

Support for async connectors. If the command declares an execute_async method, this is called. The response of this method can define HTTP status code in the JSON payload that are sent back to spiff.

Async connectors still need to implement the callback functionality as well as thread pooling etc.

instead of hoisting the 202 status up from the connector body to the top level actual http status, let's just always return 202 when the connector is async.
we will still allow the connector to do fast checks and fail, but if it wants to do that, it should return an error in the body.
then spiff-arena will check that (based on the change in this ~/spiff-arena branch).

please set up an actual connector-proxy (using ~/spiff-arena/connector-proxy-demo as a base) using an actual async connector that you develop with a execute_async function.

make sure it works:

1. with a good response (no error in the body it sends back to arena): arena should park the service task

AND

2. and with an error: arena should not park the service task, but should just mark it errored.

start up arena the connector proxy using something along the lines of run-spiff-arena command but with a custom Procfile for the different connector proxy.
