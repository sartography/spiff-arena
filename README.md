# spiff-arena

SpiffArena is a low(ish)-code software development platform for building, running, and monitoring executable diagrams.
It is intended to support Citizen Developers and to enhance their ability to contribute to the software development process.
Using tools that look a lot like flow-charts and spreadsheets, it is possible to capture complex rules in a way that everyone in your organization can see, understand, and directly execute.

Please visit the [SpiffWorkflow website](https://www.spiffworkflow.org) for a [Getting Started Guide](https://www.spiffworkflow.org/posts/articles/get_started/) to see how to use SpiffArena and try it out.
There are also additional articles, videos, and tutorials about SpiffArena and its components, including SpiffWorkflow, Service Connectors, and BPMN.js extensions.



## Backend Setup, local

Remember, if you don't need a full-on native dev experience, you can run with docker (see below), which saves you from all the native setup.
If you have issues with the local dev setup, please consult [the troubleshooting guide](https://spiff-arena.readthedocs.io/en/latest/Support/Running_Server_Locally.html).

There are three prerequisites for non-docker local development:

1. python - [asdf-vm](https://asdf-vm.com) works well for installing this.
2. poetry - `pip install poetry` works
3. mysql - the app also supports postgres. and sqlite, if you are talking local dev).

When these are installed, you are ready for:

    cd spiffworkflow-backend
    poetry install
    ./bin/recreate_db clean
    ./bin/run_server_locally

On a Mac, port 7000 (used by the backend) might be hijacked by Airplay. For those who upgraded to MacOS 12.1 and are running everything locally, your AirPlay receiver may have started on Port 7000 and your server (which uses port 7000 by default) may fail due to this port already being used. You can disable this port in System Preferences > Sharing > AirPlay receiver.


## Keycloak Setup

You will want an openid server of some sort for authentication.
There is one built in to the app that is used in the docker compose setup for simplicity, but this is not to be used in production, and non-compose defaults use a separate keycloak container by default.
You can start it like this:

    ./keycloak/bin/start_keycloak

It'll be running on port 7002
If you want to log in to the keycloak admin console, it can be found at http://localhost:7002, and the creds are admin/admin (also logs you in to the app if running the frontend)

## Frontend Setup, local

First install nodejs (also installable via asdf-vm), ideally the version in .tool-versions (but likely other versions will work). Then:

    cd spiffworkflow-frontend
    npm install
    npm start

Assuming you're running Keycloak as indicated above, you can log in with admin/admin.

## Run tests

    ./bin/run_pyl

## Run cypress automated browser tests

Get the app running so you can access the frontend at http://localhost:7001 in your browser by following the frontend and backend setup steps above, and then:

    ./bin/run_cypress_tests_locally

## Docker

For full instructions, see [Running SpiffWorkflow Locally with Docker](https://www.spiffworkflow.org/posts/articles/get_started_docker/).

The `docker-compose.yml` file is for running a full-fledged instance of spiff-arena while `editor.docker-compose.yml` provides BPMN graphical editor capability to libraries and projects that depend on SpiffWorkflow but have no built-in BPMN edit capabilities.

## Contributing

To start understanding the system, you might:

 1. Explore the demo site via the [Getting Started Guide](https://www.spiffworkflow.org/posts/articles/get_started)
 1. Clone this repo, `cd docs`, run `./bin/build`, and open your browser to [http://127.0.0.1:8000](http://127.0.0.1:8000) to view (and ideally edit!) the docs
 1. Check out our [GitHub issues](https://github.com/sartography/spiff-arena/issues), find something you like, and ask for help on discord

## Monorepo

This is a monorepo based on git subtrees that pulls together various spiffworkflow-related projects.
FYI, some scripts:

    ls bin | grep subtree

## License

SpiffArena's main components are published under the terms of the
[GNU Lesser General Public License (LGPL) Version 3](https://www.gnu.org/licenses/lgpl-3.0.txt).

## Support

You can find us on [our Discord Channel](https://discord.gg/BYHcc7PpUC).
Commercial support for SpiffWorkflow is available from [Sartography](https://sartography.com).
