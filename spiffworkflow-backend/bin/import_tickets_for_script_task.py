"""Import tickets, for use in script task."""


def main():
    """Use main to avoid global namespace."""
    import csv

    from spiffworkflow_backend.models.db import db

    from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
    from spiffworkflow_backend.models.user import UserModel
    from spiffworkflow_backend.services.process_instance_processor import (
        ProcessInstanceProcessor,
    )
    from spiffworkflow_backend.services.process_instance_service import (
        ProcessInstanceService,
    )
    from spiffworkflow_backend.models.process_instance_report import (
        ProcessInstanceReportModel,
    )

    process_model_identifier_ticket = "ticket"
    db.session.query(ProcessInstanceModel).filter(
        ProcessInstanceModel.process_model_identifier == process_model_identifier_ticket
    ).delete()
    db.session.commit()

    """Print process instance count."""
    process_instances = ProcessInstanceModel.query.filter_by(
        process_model_identifier=process_model_identifier_ticket
    ).all()
    process_instance_count = len(process_instances)
    print(f"process_instance_count: {process_instance_count}")

    columns_to_data_key_mappings = {
        "Month": "month",
        "MS": "milestone",
        "Done?": "done",
        "#": "notion_id",
        "ID": "req_id",
        "Dev Days": "dev_days",
        "Feature": "feature",
        "Feature description": "feature_description",
        "Priority": "priority",
    }
    columns_to_header_index_mappings = {}

    user = UserModel.query.first()

    with open("tests/files/tickets.csv") as infile:
        reader = csv.reader(infile, delimiter=",")

        # first row is garbage
        next(reader)

        header = next(reader)
        for column_name in columns_to_data_key_mappings:
            columns_to_header_index_mappings[column_name] = header.index(column_name)
        id_index = header.index("ID")
        priority_index = header.index("Priority")
        month_index = header.index("Month")
        print(f"header: {header}")
        for row in reader:
            ticket_identifier = row[id_index]
            priority = row[priority_index]
            month = row[month_index]
            print(f"ticket_identifier: {ticket_identifier}")
            print(f"priority: {priority}")
            # if there is no month, who cares about it.
            if month:
                process_instance = ProcessInstanceService.create_process_instance_from_process_model_identifier(
                    process_model_identifier=process_model_identifier_ticket,
                    user=user,
                    process_group_identifier="sartography-admin",
                )
                processor = ProcessInstanceProcessor(process_instance)

                processor.do_engine_steps()
                # processor.save()

                for (
                    column_name,
                    desired_data_key,
                ) in columns_to_data_key_mappings.items():
                    appropriate_index = columns_to_header_index_mappings[column_name]
                    print(f"appropriate_index: {appropriate_index}")
                    processor.bpmn_process_instance.data[desired_data_key] = row[
                        appropriate_index
                    ]

                # you at least need a month, or else this row in the csv is considered garbage
                month_value = processor.bpmn_process_instance.data["month"]
                if month_value == "" or month_value is None:
                    db.session.delete(process_instance)
                    db.session.commit()
                    continue

                processor.save()

                process_instance_data = processor.get_data()
                print(f"process_instance_data: {process_instance_data}")

    ProcessInstanceReportModel.add_fixtures()
    print("added report fixtures")


main()

# to avoid serialization issues
del main
