# spiff-arena

SpiffArena is a low(ish)-code software development platform for building, running, and monitoring executable diagrams.
It is intended to support Citizen Developers and to enhance their ability to contribute to the software development process.
Using tools that look a lot like flow-charts and spreadsheets, it is possible to capture complex rules in a way that everyone in your organization can see, understand, and directly execute.

Please visit the [SpiffWorkflow website](https://www.spiffworkflow.org) for a [Getting Started Guide](https://www.spiffworkflow.org/posts/articles/get_started/) to see how to run SpiffArena locally and try it out.
There are also additional articles, videos, and tutorials about SpiffArena and its components, including SpiffWorkflow, Service Connectors, and BPMN.js extensions.

## Backend Setup

First install python and poetry. Then:

    cd spiffworkflow-backend
    poetry install
    ./bin/recreate_db clean
    ./bin/run_server_locally

## Frontend Setup

First install nodejs, ideally the version in .tool-versions (but likely other versions will work). Then:

    cd spiffworkflow-frontend
    npm install
    npm start

## Run tests

    ./bin/run_pyl

## Run cypress automated browser tests

Get the app running so you can access the frontend at http://localhost:7001 in your browser by following the frontend and backend setup steps above, and then:

    ./bin/run_cypress_tests_locally

## Docker

For full instructions, see [Running SpiffWorkflow Locally with Docker](https://www.spiffworkflow.org/posts/articles/get_started_docker/).

The `docker-compose.yml` file is for running a full-fledged instance of spiff-arena while `editor.docker-compose.yml` provides BPMN graphical editor capability to libraries and projects that depend on SpiffWorkflow but have no built-in BPMN edit capabilities.

## Contributing

This is a monorepo based on git subtrees that pulls together various spiffworkflow-related projects.
Feel free to ignore that and drop us a pull request.
If you need to push back from the monorepo to one of the individual repos, here's an example command (and find other scripts we use in the `bin` directory):

    git subtree push --prefix=spiffworkflow-frontend git@github.com:sartography/spiffworkflow-frontend.git add_md_file

## License

SpiffArena's main components are published under the terms of the
[GNU Lesser General Public License (LGPL) Version 3](https://www.gnu.org/licenses/lgpl-3.0.txt).

## Support

You can find us on [our Discord Channel](https://discord.gg/BYHcc7PpUC).

Commercial support for SpiffWorkflow is available from [Sartography](https://sartography.com).
