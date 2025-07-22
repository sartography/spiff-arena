# Process Model Import Functionality

This document describes how to use the process model import functionality in SpiffWorkflow.

## Importing Process Models from GitHub

SpiffWorkflow allows importing process models directly from GitHub repositories. This feature is available in two places:

1. From the Process Models list view (when viewing a process group)
2. From the "Add Process Model" page

### Import Requirements

When importing a process model from GitHub:

1. The URL must be to a GitHub repository path that contains a valid process model structure
2. The URL must follow this format: `https://github.com/owner/repo/tree/branch/path/to/model`
3. The GitHub repository must be public or you must have access to it

### Import Process

1. Click the "Import from GitHub" button
2. Enter the GitHub URL for the process model directory
3. Click "Import Model"
4. If successful, you will be redirected to the imported process model

### Supported Process Model Formats

The import functionality supports standard SpiffWorkflow process model structures, including:

- BPMN diagrams
- DMN decision tables
- JSON configuration files
- Form definitions

## Troubleshooting

If the import fails, check the following:

1. Ensure the GitHub URL is correct and points to a valid process model directory
2. Verify that you have access to the repository
3. Check that the process model files are structured correctly
4. Ensure the repository contains all required files for the process model