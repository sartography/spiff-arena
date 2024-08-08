# Process Model Management

Managing your process models is similar to managing your source code.
As such, it is recommended to store these models in a version control system like Git so that you can track changes and collaborate with others.
SpiffWorkflow can integrate with Git in various ways should you so choose.

When you are starting out, you can create an empty directory for process models.
Let's say it's at `/var/tmp/my-process-models` and that you are firing up SpiffWorkflow on your local machine outside of Docker (you can absolutely use Docker if you choose):

```sh
SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR=/var/tmp/my-process-models ./bin/run_server_locally
```

When you add a process group, it will appear at `/var/tmp/my-process-models/my-awesome-process-group`.
When you are done making changes, you can commit these changes to Git.

If you want to collaborate with others on a shared environment and you want process model editing to be allowed, you can set up bidirectional syncing with Git as follows.
Editing process models locally is another perfectly good option, depending on your needs.

## Bidirectional Syncing with Git

1. Configure the environment to have a single replica for spiffworkflow-backend.
2. Make your process model repository available to the backend, potentially by:
    * Cloning your repository as the container boots, either via an init container or as part of the startup command.
    * Getting the repo onto a persistent volume that can be mounted into your container
3. Set up environment variables like the following so all changes you make will be sent to your Git remote:

    ```sh
    SPIFFWORKFLOW_BACKEND_GIT_COMMIT_ON_SAVE=true
    SPIFFWORKFLOW_BACKEND_GIT_USERNAME=automation-user
    SPIFFWORKFLOW_BACKEND_GIT_USER_EMAIL=automation-user@example.com
    SPIFFWORKFLOW_BACKEND_GIT_SOURCE_BRANCH=sandbox # this branch will get pushed with your commits
    SPIFFWORKFLOW_BACKEND_GIT_SSH_PRIVATE_KEY_PATH=/path/to/your/private/key
    SPIFFWORKFLOW_BACKEND_GIT_SSH_PRIVATE_KEY="alternate way of providing the key as a multiline string"
    ```
4. Set up a webhook so that all changes that occur outside of the app can be immediately reflected in the app.
    * This functionality supports GitHub at the moment.
    * This will be an HTTP POST to `/v1.0/github-webhook-receive`.
    * If you want to authorize the webhook, set `SPIFFWORKFLOW_BACKEND_GITHUB_WEBHOOK_SECRET` as appropriate.
    * Each webhook call from the Git remote will result in a Git pull in the backend.

## Editing Process Models Locally

Rather than editing your process models on a shared server, you can choose to make all process model changes locally.
There are other guides for running SpiffWorkflow on your local computer, so follow the one that you prefer (Docker Compose or native).
Then, when your process model repo is configured as you desire, you can run it in a read-only mode on your shared environments like dev, staging, and prod.
To do that, follow step 2 under Bidirectional Syncing with Git, but you also have an additional option of "baking the models in" to your spiffworkflow-backend image.
That is, you could choose to write a Dockerfile like:

```Dockerfile
FROM spiffworkflow-backend:some-tag
ADD my-process-models /app/process_models
```

This would allow you to create instances of your process models in your environments without needing to mount a volume or clone a repo.
If your process model repo has a `.git` directory, process instances that are created will store the commit hash in the database.
This can be particularly helpful if you have long-lived process instances.

## Process Model Promotion Strategy

Probably the best way of promoting models is to do work on a specific branch and then merge that branch into the next branch (maybe staging if you are actively changing dev).
It is also possible to promote models piecemeal.
This is activated via `SPIFFWORKFLOW_BACKEND_GIT_PUBLISH_TARGET_BRANCH`, which is for a specific use case where you want to publish specific process models from the source branch to a target Git branch, rather than promoting the entire Git branch.
A publish function appears in the UI when `SPIFFWORKFLOW_BACKEND_GIT_PUBLISH_TARGET_BRANCH` is set.
It is possibly not a recommended strategy for promoting changes, however, as it is not a standard Git workflow, and it is more error-prone in situations where multiple process models need to work together.
