#!/usr/bin/env python3
"""
Standalone diagnostic script to check for orphaned child task references.

This can be run against a live database to check if the bug exists.

Usage:
    export FLASK_APP=src.spiffworkflow_backend
    python diagnose_orphaned_children.py [process_instance_id]

If no process_instance_id is provided, it will check ALL process instances
and report which ones have orphaned children.
