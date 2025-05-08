from spiffworkflow_backend.services.jinja_service import JinjaService
import json

with open("contents.txt") as f:
    contents = f.read()
result = JinjaService.render_jinja_template(contents, task_data={"parcel_id_fields": [{"title": "1", "type": "number"}]})
print(result)
