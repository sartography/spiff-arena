# Technical Overview

## Components

```mermaid
graph TD
subgraph spiff-arena
    Backend
    Frontend
end
subgraph Backend
    subgraph SpiffWorkflow lib
    end
end
subgraph Frontend
    subgraph bpmn-js-spiffworkflow lib
    end
end
Frontend -- uses REST API --> Backend
Backend -- delegates to --> C
Backend -- persists to --> DB
DB[(mysql/postgres)]
C[Connector Proxy]
```

SpiffArena is a system that allows users to build and execute BPMN diagrams.
It is composed of three applications, [spiffworkflow-frontend](frontend), [spiffworkflow-backend](backend), and, optionally, a [connector proxy](connector_proxy).

## Source code layout

From a source code perspective, there are three repositories that may be of interest:

* [spiff-arena](https://github.com/sartography/spiff-arena) - Includes spiffworkflow-frontend, spiffworkflow-backend, and connector-proxy-demo.
* [SpiffWorkflow](https://github.com/sartography/SpiffWorkflow) - The core SpiffWorkflow library, 10 years old, Python, awesome, [well-documented](https://spiffworkflow.readthedocs.io/).
* [bpmn-js-spiffworkflow](https://github.com/sartography/bpmn-js-spiffworkflow) - The frontend library that extends bpmn-js to work with SpiffWorkflow.
