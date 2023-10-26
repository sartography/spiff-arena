
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend import create_app
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor

app = create_app()
with app.app_context():
    pi = ProcessInstanceModel.query.filter_by(id=3).first()
    proc = ProcessInstanceProcessor(pi)
    ProcessInstanceService.ready_user_task_has_associated_timer(proc)
