# Troubleshooting: Running Server Locally

When setting up the SpiffWorkflow backend project locally, you might encounter issues related to the `sample-process-models` directory.
This documentation aims to address those concerns.

## Problem

While following the instructions provided in the repository to set up the SpiffWorkflow backend project locally, you may find that the script `./bin/run_server_locally` expects the `sample-process-models` directory to be present.
However, this directory might not be immediately available in the repository.

## Solutions

### 1. Clone the `sample-process-models` Repository

The `sample-process-models` directory refers to a separate repository.
To resolve the issue:

- Navigate to [https://github.com/sartography/sample-process-models](https://github.com/sartography/sample-process-models).

- Clone the repository right next to `spiff-arena`.

- Run the `./bin/run_server_locally` script.

### 2. Use Any Git Repository

If you prefer not to use the `sample-process-models` directory or want to start from scratch:

- Locate or create a git repository.

- Run the following command with the path to your chosen repository:

   ```
   SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR=/path/to/any/git/repo ./bin/run_server_locally
   ```

### 3. Use Docker Compose

For a potentially faster setup:

- Follow the guide at [https://www.spiffworkflow.org/posts/articles/get_started_docker](https://www.spiffworkflow.org/posts/articles/get_started_docker).

- Use the provided commands to run the server with Docker Compose.

### 4. Mac Install Issues

First, follow the README.md at the root of the spiff-arena repo.
If you're on a Mac and trying to run natively (this might also apply elsewhere) and get errors when running `poetry install`, many of these issues are related to relational database engine libraries.
Many people have encountered these problems, so hopefully, the solution to your specific issue is easy to find, but this is not always the case.
You may need to install additional system dependencies:

    brew install mysql-client pkg-config
    export PKG_CONFIG_PATH="$(brew --prefix)/opt/mysql-client/lib/pkgconfig"
    pip install mysqlclient
    pip install psycopg2

One person decided that mysqlclient and psycopg2 were more trouble than they were worth and removed them from the pyproject.toml, opting instead to run `poetry add pymysql`.
If you are using mysql, psycopg2 is not necessary, and pymysql is a pure Python implementation of the MySQL client library.
In that case, Python won't recognize MySQLdb as a module, so after the above installs (which you would do pre-Poetry), add these lines to __init__.py in the backend project:

```python
import pymysql
pymysql.install_as_MySQLdb()
```

### 5. Access Hosted Version of Spiff

If you prefer not to install anything locally:

- Navigate to [https://www.spiffworkflow.org/posts/articles/get_started](https://www.spiffworkflow.org/posts/articles/get_started).

- Access a version of Spiff hosted on the internet.

Setting up the SpiffWorkflow backend project locally can be straightforward once you're aware of the dependencies and options available.
Whether you choose to clone the `sample-process-models` repository, use a different git repository, or opt for Docker Compose, the solutions provided should help you get started without any hitches.

If you encounter further issues, always refer back to the repository's README or seek assistance from our Discord community.
