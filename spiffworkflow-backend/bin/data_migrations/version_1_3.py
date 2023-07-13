
from spiffworkflow_backend import create_app
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models import bpmn_process_definition
from spiffworkflow_backend.models.task_definition import TaskDefinitionModel

def main():

    def run():
        app = create_app()
        with app.app_context():
            task_definitions = self.get_relevant_task_definitions()
            for tdm in task_definitions:
                self.process_task_definition(tdm)

    def get_relevant_task_definitions(self) -> list[TaskDefinitionModel]:
        task_definitions = TaskDefinitionModel.query.filter_by(typename='_BoundaryEventParent').all()
        return task_definitions


    def process_task_definition(task_definition: TaskDefinitionModel) -> None:
        task_definition.typename = 'BoundaryEventSplit'
        task_definition.bpmn_identifier = task_definition.bpmn_identifier.replace('BoundaryEventParent', 'BoundaryEventSplit')

        properties_json = task_definition.properties_json
        properties_json.pop('main_child_task_spec')
        properties_json['typename'] = task_definition.typename
        properties_json['name'] = task_definition.bpmn_identifier
        task_definition.properties_json = properties_json
        db.sesison.add(task_definition)

        join_properties_json = {
            "name": task_definition.bpmn_identifier.replace('BoundaryEventSplit', 'BoundaryEventJoin'),
            "manual": False,
            "bpmn_id": None,
            "lookahead": 2,
            "inputs": properties_json['outputs'],
            "outputs": [],
            "split_task": task_definition.bpmn_identifier,
            "threshold": None,
            "cancel": True,
            "typename": "BoundaryEventJoin"
        }

        join_task_definition = TaskDefinitionModel(
            bpmn_process_definition_id=task_definition.bpmn_process_definition_id,
            bpmn_identifier=join_properties_json['name'],
            typename=join_properties_json['typename'],
            properties_json=join_properties_json,
        )
        db.session.add(join_task_definition)

        for parent_bpmn_identifier in properties_json['inputs']:
            parent_task_definition = TaskDefinitionModel.query.filter_by(bpmn_identifier=parent_bpmn_identifier, bpmn_process_definition=task_definition.bpmn_process_definition_id).first()
            parent_task_definition.properties_json['outputs'] = [name.replace('BoundaryEventParent', 'BoundaryEventSplit') for name in parent_task_definition.properties_json['outputs']]
            db.session.add(parent_task_definition)

        for child_bpmn_identifier in properties_json['outputs']:
            child_task_definition = TaskDefinitionModel.query.filter_by(bpmn_identifier=child_bpmn_identifier, bpmn_process_definition=task_definition.bpmn_process_definition_id).first()
            child_task_definition.properties_json['outputs'].append(join_task_definition.bpmn_identifier)
            child_task_definition.properties_json['inputs'] = [name.replace('BoundaryEventParent', 'BoundaryEventSplit') for name in child_task_definition.properties_json['inputs']]
            db.session.add(child_task_definition)

    # def update_tasks(wf):
    #     new_tasks = {}
    #     for task in wf['tasks'].values():
    #         if task['task_spec'].endswith('BoundaryEventParent'):
    #             task['task_spec'] = task['task_spec'].replace('BoundaryEventParent', 'BoundaryEventSplit')
    #             completed = all([ wf['tasks'][child]['state'] in [64, 256] for child in task['children'] ])
    #             for child in task['children']:
    #                 child_task = wf['tasks'][child]
    #                 if child_task['state'] < 8:
    #                     # MAYBE, LIKELY, FUTURE: use parent state
    #                     state = child_task['state']
    #                 elif child_task['state'] < 64:
    #                     # WAITING, READY, STARTED (definite): join is FUTURE
    #                     state = 4
    #                 elif child_task['state'] == 64:
    #                     # COMPLETED: if the join is not finished, WAITING, otherwise COMPLETED
    #                     state = 64 if completed else 8
    #                 elif child_task['state'] == 128:
    #                     # ERROR: we don't know what the original state was, but we can't proceed through the gateway
    #                     state = 8
    #                 else:
    #                     # Cancelled tasks don't have children
    #                     continue
    #                 new_task = {
    #                     'id': str(uuid4()),
    #                     'parent': child_task['id'],
    #                     'children': [],
    #                     'state': state,
    #                     'task_spec': task['task_spec'].replace('BoundaryEventSplit', 'BoundaryEventJoin'),
    #                     'last_state_change': None,
    #                     'triggered': False,
    #                     'internal_data': {},
    #                     'data': {},
    #                 }
    #                 child_task['children'].append(new_task['id'])
    #                 new_tasks[new_task['id']] = new_task
    #     
    #     wf['tasks'].update(new_tasks)
    #     pass
    #
    # update_specs(dct['spec'])
    # for sp_spec in dct['subprocess_specs'].values():
    #     update_specs(sp_spec) 
    #
    # update_tasks(dct)
    # for sp in dct['subprocesses'].values():
    #     update_tasks(sp)

main()
