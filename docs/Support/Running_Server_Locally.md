# Troubleshooting: Running Server Locally

When setting up the SpiffWorkflow backend project locally, you might encounter issues related to the `sample-process-models` directory. This documentation aims to address those concerns.

## Problem

While following the instructions provided in the repository to set up the SpiffWorkflow backend project locally, you may find that the script `./bin/run_server_locally` expects the `sample-process-models` directory to be present. However, this directory might not be immediately available in the repository.

## Solutions

### 1. Clone the `sample-process-models` Repository

The `sample-process-models` directory refers to a separate repository. To resolve the issue:

- Navigate to [https://github.com/sartography/sample-process-models](https://github.com/sartography/sample-process-models).

- Clone the repository right next to `spiff-arena`.

- Run the `./bin/run_server_locally` script.

### 2. Use Any Git Repository

If you prefer not to use the `sample-process-models` directory or want to start from scratch:

- Locate or create a git repository.

- Run the following command with the path to your chosen repository

   ```
   SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR=/path/to/any/git/repo ./bin/run_server_locally
   ```

### 3. Use Docker Compose

For a potentially faster setup:

- Follow the guide at [https://www.spiffworkflow.org/posts/articles/get_started_docker](https://www.spiffworkflow.org/posts/articles/get_started_docker).

- Use the provided commands to run the server with Docker Compose.

### 4. Access Hosted Version of Spiff

If you prefer not to install anything locally:

- Navigate to [https://www.spiffworkflow.org/posts/articles/get_started](https://www.spiffworkflow.org/posts/articles/get_started).
- Access a version of Spiff hosted on the internet.



Setting up the SpiffWorkflow backend project locally can be straightforward once you're aware of the dependencies and options available. Whether you choose to clone the `sample-process-models` repository, use a different git repository, or opt for Docker Compose, the solutions provided should help you get started without any hitches. 

If you encounter further issues, always refer back to the repository's README or seek assistance from our discord community.