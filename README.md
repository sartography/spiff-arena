# spiff-arena

SpiffArena is a low(ish)-code software development platform for building, running, and monitoring executable diagrams.
It is intended to support Citizen Developers and to enhance their ability to contribute to the software development process.
Using tools that look a lot like flow-charts and spreadsheets, it is possible to capture complex rules in a way that everyone in your organization can see, understand, and directly execute.

Please visit the [SpiffWorkflow website](https://www.spiffworkflow.org) for a [Getting Started Guide](https://www.spiffworkflow.org/posts/articles/get_started/) to see how to use SpiffArena and try it out.
There are also additional articles, videos, and tutorials about SpiffArena and its components, including SpiffWorkflow, Service Connectors, and BPMN.js extensions.

## Backend Setup

First install python, poetry, and mysql. Then:

    cd spiffworkflow-backend
    poetry install
    ./bin/recreate_db clean
    ./bin/run_server_locally

Note: if you're on a Mac and trying to run native (might translate elsewhere) running python 3 and get errors with mysqlclient and psycopgen2, you may need to install mysql-client, pkg-config, mysqlclient, and psycopgen2 (and remove mysqlclient and psycopgen2 from the pyproject.toml or Poetry will try to build them and crash). 

    brew install mysql-client pkg-config
    export PKG_CONFIG_PATH="$(brew --prefix)/opt/mysql-client/lib/pkgconfig"
    pip install mysqlclient
    pip install psycopg2

On a Mac, port 7000 (used by the app) might be hijacked by Airplay. See the Docker section below. 

Remember, if you don't need a full-on native dev experience, you can run the docker image, which saves you from all the native setup.

## Keycloak Setup

You will want an openid server of some sort.
There is one built in to the app that is used in the docker compose setup for simplicity, but non-compose defaults use a separate keycloak container by default.
You can start it like this:

    ./keycloak/bin/start_keycloak

It'll be running on port 7002 (if you want to log into the keycloak admin, localhost:7002). 
Creds = admin/admin (also logs you into the app if running the front end)

## Frontend Setup

First install nodejs, ideally the version in .tool-versions (but likely other versions will work). Then:

    cd spiffworkflow-frontend
    npm install
    npm start

Assuming you're running KeyCloak as indicated above, login will be admin/admin.

## Run tests

    ./bin/run_pyl

## Run cypress automated browser tests

Get the app running so you can access the frontend at http://localhost:7001 in your browser by following the frontend and backend setup steps above, and then:

    ./bin/run_cypress_tests_locally

## Docker

For full instructions, see [Running SpiffWorkflow Locally with Docker](https://www.spiffworkflow.org/posts/articles/get_started_docker/).

The `docker-compose.yml` file is for running a full-fledged instance of spiff-arena while `editor.docker-compose.yml` provides BPMN graphical editor capability to libraries and projects that depend on SpiffWorkflow but have no built-in BPMN edit capabilities.

Note: For those who upgraded to MacOS 12.1 and are running everything locally, your AirPlay receiver may have started on Port 7000 and your docker (or anything requesting port 7000) may fail due to this port already being used. You can disable this port in System Preferences > Sharing > AirPlay receiver. 

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

