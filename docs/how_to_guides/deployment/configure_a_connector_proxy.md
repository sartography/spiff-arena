# Configure a Connector Proxy

## Setting the Environment Variable

Once a `Connector Proxy` has been deployed, to integrate it with SpiffArena, we simply need to update an environment variable and restart the backend.
If you're using the [Getting Started Guide](https://www.spiffworkflow.org/posts/articles/get_started/), open the docker-compose.yml file; otherwise, edit the environment variable in the way that is appropriate for your deployment.
The variable we need to change is called `SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_URL`.

Here's an example diff using the function URL from the AWS tutorial:

```
diff --git a/docker-compose.yml b/docker-compose.yml
index 95b87b39..7d55c492 100644
--- a/docker-compose.yml
+++ b/docker-compose.yml
@@ -26,7 +26,7 @@ services:
       SPIFFWORKFLOW_BACKEND_URL: "http://localhost:${SPIFF_BACKEND_PORT:-8000}"

       SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR: "/app/process_models"
-      SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_URL: "http://spiffworkflow-connector:8004"
+      SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_URL: "https://crbxgaopinfxqscntkqixjbl4e0gigpm.lambda-url.us-east-1.on.aws"
       SPIFFWORKFLOW_BACKEND_DATABASE_URI: "mysql+mysqlconnector://root:${SPIFF_MYSQL_PASS:-my-secret-pw}@spiffworkflow-db:${SPIFF_MYSQL_PORT:-8003}/spiffworkflow_backend_development"
       SPIFFWORKFLOW_BACKEND_LOAD_FIXTURE_DATA: "false"
       SPIFFWORKFLOW_BACKEND_OPEN_ID_CLIENT_ID: "spiffworkflow-backend"

```

To restart:

```
docker compose down
docker compose up -d
```

## Testing

Create a new process model as described in the [Getting Started Guide](https://www.spiffworkflow.org/posts/articles/get_started/).
Add a `Service Task` and in its properties panel, you will see a dropdown from which you can select the connector in your `Connector Proxy` to call.
In this demo, we deployed HTTP GET and POST connectors:

![Screenshot from 2023-04-06 16-38-02](https://user-images.githubusercontent.com/100367399/230489492-63cf88bf-7533-4160-95cb-d6194506dd5d.png)

Choose the `http/GetRequest` operator ID and enter the [dog fact API](https://dog-api.kinduff.com/api/facts) URL.
Remember to quote it since parameters are evaluated as Python expressions.

![Screenshot from 2023-04-06 16-50-42](https://user-images.githubusercontent.com/100367399/230491661-abdfdd3a-48f5-4f50-b6e5-9e3a5f562961.png)

Run the process and once it's complete, you can see the response in the workflow:

![Screenshot from 2023-04-06 16-49-53](https://user-images.githubusercontent.com/100367399/230491713-9d3f9bd0-f284-4004-b00c-cb6dc94b53df.png)

You have successfully configured a `Connector Proxy` for use with `SpiffArena`.
You made a call from a workflow to get a dog fact.
Now, imagine if that call was to communicate with an external system relevant to your business processes.
