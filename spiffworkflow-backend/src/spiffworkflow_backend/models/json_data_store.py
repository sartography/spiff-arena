from dataclasses import dataclass

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


#@dataclass
class JSONDataStoreModel(): #SpiffworkflowBaseDBModel):
   #__tablename__ = "json_data_store"

   id: int #= db.Column(db.Integer, primary_key=True)
   name: str #= db.Column(db.String(255), index=True)
   location: str #= db.Column(db.String(255))
   schema: dict #= db.Column(db.JSON)
   data: dict #= db.Column(db.JSON)
   updated_at_in_seconds: int #= db.Column(db.Integer)
   created_at_in_seconds: int #= db.Column(db.Integer)
 
