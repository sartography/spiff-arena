"""
This script attempts to replicate the duplicate key issue with bpmn_process_definition table.
Run it using: ./bin/run_local_python_script test_duplicate_key_issue.py
"""

import json
import multiprocessing
import time
from flask import current_app
from sqlalchemy.dialects import mysql
from sqlalchemy.dialects.mysql import insert as mysql_insert

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel


def insert_record(process_hash):
    """Insert a record with the given hash, demonstrating the issue."""
    test_record = {
        "single_process_hash": "test_single_hash",
        "full_process_model_hash": process_hash,
        "bpmn_identifier": "test_identifier",
        "bpmn_name": "Test Process",
        "properties_json": "{}",
        "bpmn_version_control_type": "",
        "bpmn_version_control_identifier": "",
    }
    
    # The approach using SQLAlchemy ORM
    print(f"Process {process_hash}: Inserting record")
    
    # Method 1: The current approach in the codebase
    new_stuff = test_record.copy()
    del new_stuff["full_process_model_hash"]
    
    insert_stmt = mysql_insert(BpmnProcessDefinitionModel).values(test_record)
    on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(**new_stuff)
    
    print(f"Process {process_hash}: SQL to execute:")
    print(on_duplicate_key_stmt.compile(dialect=mysql.dialect()))
    
    try:
        db.session.execute(on_duplicate_key_stmt)
        db.session.commit()
        print(f"Process {process_hash}: Record inserted/updated successfully")
    except Exception as e:
        db.session.rollback()
        print(f"Process {process_hash}: Error: {str(e)}")

def direct_sql_insert(process_hash):
    """Try direct SQL execution."""
    test_record = {
        "single_process_hash": "test_direct_hash",
        "full_process_model_hash": process_hash,
        "bpmn_identifier": "test_direct_identifier",
        "bpmn_name": "Test Direct Process",
        "properties_json": json.dumps({}),
    }
    
    print(f"Process {process_hash} Direct SQL: Inserting record")
    
    from sqlalchemy import text
    sql = text("""
    INSERT INTO bpmn_process_definition 
    (single_process_hash, full_process_model_hash, bpmn_identifier, bpmn_name, properties_json) 
    VALUES (:single_process_hash, :full_process_model_hash, :bpmn_identifier, :bpmn_name, :properties_json)
    ON DUPLICATE KEY UPDATE 
    single_process_hash = :single_process_hash, 
    bpmn_identifier = :bpmn_identifier, 
    bpmn_name = :bpmn_name, 
    properties_json = :properties_json
    """)
    
    try:
        db.session.execute(sql, test_record)
        db.session.commit()
        print(f"Process {process_hash} Direct SQL: Record inserted/updated successfully")
    except Exception as e:
        db.session.rollback()
        print(f"Process {process_hash} Direct SQL: Error: {str(e)}")

def process_task(hash_value, delay=0):
    """Process task with potential delay to create race condition."""
    # Import here to avoid circular imports
    from spiffworkflow_backend import create_app
    
    # Create a Flask app context
    app = create_app()
    with app.app.app_context():
        # Add a delay to help create race conditions
        if delay:
            print(f"Process {hash_value}: Sleeping for {delay} seconds")
            time.sleep(delay)
        
        # Try inserting using the SQLAlchemy approach
        insert_record(hash_value)
        
        # Try inserting using direct SQL
        direct_sql_insert(hash_value)

def run_concurrent_processes():
    """Run multiple processes concurrently to create race condition."""
    # Use the same hash for all processes to create conflicts
    hash_value = "test_duplicate_hash"
    
    # Clean up first to ensure we're starting fresh
    clean_up_existing_records(hash_value)
    
    # Create multiple processes with different delays
    processes = []
    for i in range(5):
        p = multiprocessing.Process(
            target=process_task, 
            args=(hash_value, i * 0.1)  # Add increasing delays
        )
        processes.append(p)
        p.start()
    
    # Wait for all processes to complete
    for p in processes:
        p.join()

def clean_up_existing_records(hash_value):
    """Clean up any existing records before testing."""
    from spiffworkflow_backend import create_app
    
    app = create_app()
    with app.app.app_context():
        try:
            BpmnProcessDefinitionModel.query.filter_by(full_process_model_hash=hash_value).delete()
            db.session.commit()
            print(f"Cleaned up existing records with hash {hash_value}")
        except Exception as e:
            db.session.rollback()
            print(f"Error cleaning up: {str(e)}")

def print_current_records(hash_value):
    """Print current records with the given hash."""
    from spiffworkflow_backend import create_app
    
    app = create_app()
    with app.app.app_context():
        records = BpmnProcessDefinitionModel.query.filter_by(full_process_model_hash=hash_value).all()
        print(f"Found {len(records)} records with hash {hash_value}")
        for record in records:
            print(f"  ID: {record.id}, Single Hash: {record.single_process_hash}, BPMN ID: {record.bpmn_identifier}")

def compare_approaches():
    """Compare different ON DUPLICATE KEY approaches."""
    from spiffworkflow_backend import create_app
    
    app = create_app()
    with app.app.app_context():
        # Clean up test records
        from sqlalchemy import text
        db.session.execute(text("DELETE FROM bpmn_process_definition WHERE bpmn_identifier LIKE 'test_approach%'"))
        db.session.commit()
        
        # Test data
        test_hash = "test_approach_hash"
        test_data = {
            "single_process_hash": "test_approach_single_hash",
            "full_process_model_hash": test_hash,
            "bpmn_identifier": "test_approach_identifier",
            "bpmn_name": "Test Approach Process",
            "properties_json": "{}",
            "bpmn_version_control_type": "",
            "bpmn_version_control_identifier": "",
        }
        
        # Approach 1: Current approach (possibly problematic)
        print("\nApproach 1: Current approach in codebase")
        new_stuff = test_data.copy()
        del new_stuff["full_process_model_hash"]
        
        insert_stmt = mysql_insert(BpmnProcessDefinitionModel).values(test_data)
        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(**new_stuff)
        
        print("SQL to execute:")
        print(on_duplicate_key_stmt.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))
        
        try:
            db.session.execute(on_duplicate_key_stmt)
            db.session.commit()
            print("Success with Approach 1")
        except Exception as e:
            db.session.rollback()
            print(f"Error with Approach 1: {str(e)}")
            
        # Approach 2: Direct SQL with excluded full_process_model_hash
        print("\nApproach 2: Direct SQL with excluded full_process_model_hash")
        test_data["bpmn_identifier"] = "test_approach_identifier_2"
        
        sql = text("""
        INSERT INTO bpmn_process_definition 
        (single_process_hash, full_process_model_hash, bpmn_identifier, bpmn_name, properties_json, bpmn_version_control_type, bpmn_version_control_identifier) 
        VALUES (:single_process_hash, :full_process_model_hash, :bpmn_identifier, :bpmn_name, :properties_json, :bpmn_version_control_type, :bpmn_version_control_identifier)
        ON DUPLICATE KEY UPDATE 
        single_process_hash = VALUES(single_process_hash),
        bpmn_identifier = VALUES(bpmn_identifier),
        bpmn_name = VALUES(bpmn_name),
        properties_json = VALUES(properties_json),
        bpmn_version_control_type = VALUES(bpmn_version_control_type),
        bpmn_version_control_identifier = VALUES(bpmn_version_control_identifier)
        """)
        
        print("SQL to execute:")
        print(sql)
        
        try:
            db.session.execute(sql, test_data)
            db.session.commit()
            print("Success with Approach 2")
        except Exception as e:
            db.session.rollback()
            print(f"Error with Approach 2: {str(e)}")
            
        # Print the results
        records = BpmnProcessDefinitionModel.query.filter(
            BpmnProcessDefinitionModel.bpmn_identifier.like('test_approach%')
        ).all()
        print("\nResults:")
        for record in records:
            print(f"ID: {record.id}, BPMN ID: {record.bpmn_identifier}, Hash: {record.full_process_model_hash}")

def main():
    print("===== TESTING DUPLICATE KEY ISSUE =====")
    
    # Use multiprocessing to simulate concurrent requests
    run_concurrent_processes()
    
    # Check what records exist after the concurrent inserts
    print_current_records("test_duplicate_hash")
    
    # Compare different approaches
    print("\n===== COMPARING DIFFERENT APPROACHES =====")
    compare_approaches()


if __name__ == "__main__":
    main()