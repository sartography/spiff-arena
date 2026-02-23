When we added additional default parameters to be sent to all connectors (call back urls, process intance ids) it broke many of the connectors we are using - we are now getting an "unexpected keyword argument" when calling things like GetRequestV2.

perhaps spif-arena connector-proxy-demo - or the aggreget-connector-proxy code base, or built into the direct http call now.
connector-proxy-demo directory in arena depends on the http connector.  And I think this must be what is being used for Spiff-Demo, where it is broken.

Get everything running, including arena and the connector proxy, get a process model that uses a service task (which delegates to connector, hopefully, not getting handled by backend itself), and replicate the issue via the arena api (call_api script or similar).
then probably fix the connector proxy demo codebase to accept the params, re-run the failing integration test (really a script of some sort), and ensure it works.
