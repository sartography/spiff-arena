#!/usr/bin/env python3
"""
Simple test script to verify the deferred logging implementation works correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.api_log_model import APILogModel
from spiffworkflow_backend.utils.api_logging import log_api_interaction, setup_deferred_logging

# Create a minimal Flask app for testing
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SPIFFWORKFLOW_BACKEND_API_LOGGING_ENABLED'] = True
db.init_app(app)
setup_deferred_logging(app)

@log_api_interaction
def test_function():
    """A simple function to test the decorator."""
    print("test_function called")
    return {"message": "success"}, 200

def main():
    with app.app_context():
        # Create the database tables
        db.create_all()

        # Clear any existing logs
        db.session.query(APILogModel).delete()
        db.session.commit()

        print("Before calling test_function")
        print(f"Log count: {db.session.query(APILogModel).count()}")

        # Test the decorated function
        with app.test_request_context('/test', method='POST'):
            result = test_function()
            print(f"Function result: {result}")

        print("After calling test_function")
        print(f"Log count: {db.session.query(APILogModel).count()}")

        # Check the logs
        logs = db.session.query(APILogModel).all()
        if logs:
            log = logs[0]
            print(f"Log entry created: endpoint={log.endpoint}, method={log.method}, status={log.status_code}")
            print("✅ Deferred logging works correctly!")
        else:
            print("❌ No log entries found - deferred logging not working")

if __name__ == '__main__':
    main()