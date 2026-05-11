We have a new service task retries feature.
We added some parsing code to ~/spiff-arena in this branch at src/spiffworkflow_backend/services/custom_parser.py
We think maybe this parsing belongs in ~/SpiffWorkflow (lib used by arena).

We'd also like to support this feature in ~/bpmn-js-spiffworkflow.

there is a run-spiff-arena command.
might need to run use_local_bpmn_js_spiffworkflow in arena/spiffworkflow-frontend/bin (from frontend) to use the updated bpmn-js-spiff... lib
