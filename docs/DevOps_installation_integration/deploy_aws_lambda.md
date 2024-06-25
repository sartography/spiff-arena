# Deploying a Connector Proxy as an AWS Lambda Function

This guide shows you how to deploy the demo `Connector Proxy` as an `AWS Lambda Function` and integrate it with [SpiffArena](https://www.spiffworkflow.org/pages/spiffarena/).
We will use the [Getting Started Guide](https://www.spiffworkflow.org/posts/articles/get_started/) as the basis for integration, but the steps should easily map to any custom installation.

It is assumed that you have access to log in to the AWS Console and can create/deploy Lambda functions.

## Building the Zip

One method of deploying a Lambda function is by uploading a zip file containing the source code or executable.
Run the following command in the root of [this repository](https://github.com/sartography/connector-proxy-lambda-demo):

```
make zip
```

This will create a zip file containing the [Lambda entry point function](https://github.com/sartography/connector-proxy-lambda-demo/blob/main/connector_proxy_lambda_demo/lambda_function.py#L5) and all the dependencies needed to execute the connectors.
For this example, the libraries [spiffworkflow-proxy](https://github.com/sartography/spiffworkflow-proxy) for discovering connectors and [connector-http](https://github.com/sartography/connector-http), an example connector that provides HTTP get and post requests, are used.

Once `make zip` completes, `connector_proxy_lambda_demo.zip` will be available in the repository root.

## Creating the Lambda Function

Log in to the AWS Console and navigate to the Lambda section.

![Screenshot from 2023-04-06 15-19-35](https://user-images.githubusercontent.com/100367399/230482600-bf5f72b4-f499-4d44-8f6b-814d8e4c67d2.png)

From there, choose `Create function`.

![Screenshot from 2023-04-06 15-22-39](https://user-images.githubusercontent.com/100367399/230482607-ad561180-9a4d-4ad1-8e4c-c97903f99100.png)

Opt for `Author from scratch` and select the most recent Python runtime.

![Screenshot from 2023-04-06 15-23-19](https://user-images.githubusercontent.com/100367399/230482609-8bece818-a41f-4f37-99c4-d9d10bef4d54.png)

Under `Advanced Settings`, check `Enable function URL`.
For this demo, we will use the `NONE` auth type to keep things simple.

![Screenshot from 2023-04-06 15-24-12](https://user-images.githubusercontent.com/100367399/230482613-8fa6c8ef-5035-4a77-9670-f7211bf92cc0.png)

After clicking the `Create function` button, you will be taken to your new Lambda function:

![Screenshot from 2023-04-06 16-02-11](https://user-images.githubusercontent.com/100367399/230482618-cf4cf088-3629-4832-9a3d-d81f29842aff.png)

In the bottom right of the first section is a link to your Lambda's function URL.
Click it for a hello world response.

![Screenshot from 2023-04-06 16-09-08](https://user-images.githubusercontent.com/100367399/230484874-7529b786-da15-4a2c-8731-3780712bc0ef.png)

## Deploying the Lambda Function

If you scroll down, you will see a section with the example code created with your Lambda function.
We are going to replace this with the contents of our zip file.
Choose `Upload from` and select `.zip file`.

![Screenshot from 2023-04-06 16-09-34](https://user-images.githubusercontent.com/100367399/230484774-c0b93e1a-e34d-47b3-813f-03598d5bd631.png)

After a confirmation dialog, you will see that your Lambda has been updated:

![Screenshot from 2023-04-06 16-12-05](https://user-images.githubusercontent.com/100367399/230485279-425e71ca-1c7f-4da3-b5e0-2fd2a464d746.png)

Click your function URL again to see a greeting from our deployed Connector Proxy.

## Integrating With SpiffArena

Congratulations, your Connector Proxy has been deployed as a Lambda function.
For information on configuring SpiffArena to use the new Connector Proxy URL, please see [Configure a Connector Proxy](configure_connector_proxy).
