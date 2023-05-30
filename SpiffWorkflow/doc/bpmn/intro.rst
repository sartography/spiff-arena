BPMN Workflows
==============

The basic idea of SpiffWorkflow is that you can use it to write an interpreter
in Python that creates business applications from BPMN models.  In this section,
we'll develop a model of a reasonably complex process and show how to run it.

We expect that readers will fall into two general categories:

- People with a background in BPMN who might not be very familiar Python
- Python developers who might not know much about BPMN

This section of the documentation provides an example that (hopefully) serves
the needs of both groups.  We will introduce some of the more common BPMN
elements and show how to build a simple workflow runner around them.

SpiffWorkflow does heavy-lifting such as keeping track of task dependencies and
states and providing the ability to serialize or deserialize a workflow that
has not been completed.  The developer will write code for displaying workflow
state and presenting tasks to users of their application.

All the Python code and BPMN models used here are available in an example
project called `spiff-example-cli <https://github.com/sartography/spiff-example-cli>`_.

Quickstart
----------

Check out the code in `spiff-example-cli <https://github.com/sartography/spiff-example-cli>`_
and follow the instructions to set up an environment to run it in.

Run the sample workflow we built up using our example application with the following
command:

.. code-block:: console

   ./spiff-bpmn-runner.py -c order_collaboration \
        -d bpmn/tutorial/{product_prices,shipping_costs}.dmn \
        -b bpmn/tutorial/{top_level_multi,call_activity_multi}.bpmn

.. sidebar:: BPMN Runner

  The example app provides a utility for running BPMN Diagrams from the command
  line that will allow you to introspect a bit on a running process.  You
  can see the options available by running:

     ./spiff-bpmn-runner.py --help

The code in the workflow runner and the models in the bpmn directory of the
repository will be discussed in the remainder of this tutorial.


Supported BPMN Elements
-----------------------

.. toctree::
   :maxdepth: 3

   tasks
   gateways
   organization
   events
   data
   multiinstance

Putting it All Together
-----------------------

.. toctree::
   :maxdepth: 2

   synthesis

Features in More Depth
----------------------

.. toctree::
   :maxdepth: 2

   advanced

Custom Task Specs
-----------------

.. toctree::
   :maxdepth: 2

   custom_task_spec

Exceptions
----------

.. toctree::
   :maxdepth: 2

   errors

Camunda Editor Support
----------------------

.. toctree::
   :maxdepth: 2

   camunda/support
