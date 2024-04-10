# Process Model Management

Managing your process models is similar to managing your source code.
As such, it is recommended to store these models in a version control system like Git so that you can track changes and collaborate with others.
SpiffWorkflow can integrate with git in various ways should you so choose.

When you are starting out, you can create an empty directory for process models.
Let's say it's at `/var/tmp/my-process-models` and that you are firing up SpiffWorkflow on your local machine outside of docker (you can absolutely use docker if you choose):

```sh
SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR=/var/tmp/my-process-models ./bin/run_server_locally
```

When you add a process group, it will appear at `/var/tmp/my-process-models/my-awesome-process-group`.
When you are done making changes, you can commit these changes to git.

If you want to collaborate with others on a shared environment and you want process model editing to be allowed, you can set up bidirectional syncing with git as follows.
Editing Process Models locally is another perfectly good option, depending on your needs.

## Bidirectional Syncing with Git

1. Configure the environment to have a single replica for spiffworkflow-backend.
1. Make your process model repository available to backend, potentially by:
    * Cloning your repository as the container boots, either via an init container or as part of the startup command.
    * Getting the repo onto a persistent volume that can be mounted into your container
3. Set up environment variables like the following so all changes you make will be sent to your git remote:

    ```sh
    SPIFFWORKFLOW_BACKEND_GIT_COMMIT_ON_SAVE=true
    SPIFFWORKFLOW_BACKEND_GIT_USERNAME=automation-user
    SPIFFWORKFLOW_BACKEND_GIT_USER_EMAIL=automation-user@example.com
    SPIFFWORKFLOW_BACKEND_GIT_SOURCE_BRANCH=sandbox # this branch will get pushes with your commits
    ```
4. Set up a webhook so that all changes that occur outside of the app can be immediately reflected in the app.
    * This functionality supports github at the moment.
    * This will be an http POST to `/v1.0/github-webhook-receive`.
    * If you want to authorize the webhook, set SPIFFWORKFLOW_BACKEND_GITHUB_WEBHOOK_SECRET as appropriate.
    * Each webhook call from the git remote will result in a git pull in the backend.

## Editing Process Models locally
Rather than editing your process models on a shared server, you can choose to make all process model changes locally.
There are other guides for running SpiffWorkflow on your local computer, so follow the one that you prefer (docker compose or native).
Then, when your process model repo is configured as you desire, you can run it in a read only mode on your shared environments like dev, staging, and prod.
To do that, follow step 2 under Bidirectional Syncing with Git, but you also have an additional option of "baking the models in" to your spiffworkflow-backend image.
That is, you could choose to write a Dockerfile like:
```Dockerfile
FROM spiffworkflow-backend:some-tag
ADD my-process-models /app/process_models
```
This would allow you to create instances of your process models in your environments without needing to mount a volume or clone a repo.
If your process model repo has a `.git` directory, process instances that are created will store the commit hash in the database.
This can be particularly helpful if you have long-lived process instances.
