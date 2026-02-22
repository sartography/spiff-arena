When we added additional default parameters to be sent to all connectors (call back urls, process intance ids) it broke many of the connectors we are using - we are now getting an "unexpected keyword argument" when calling things like GetRequestV2.

perhaps spif-arena connector-proxy-demo - or the aggreget-connector-proxy code base, or built into the direct http call now.
connector-proxy-demo directory in arena depends on the http connector.  And I think this must be what is being used for Spiff-Demo.

Get everything running, replicate the issue, and fix.
