# Process Model Import Feature Specification

**Implementation Status:** Phase 1 completed

## Overview

The Process Model Import feature allows users to pull process models from external sources rather than creating them from scratch. This document outlines the requirements, design considerations, and implementation approaches for this feature.

## Feature Requirements

### Core Functionality

1. **Import Sources**
   - Public URLs to process model repositories
   - GitHub URLs to repositories or specific directories
   - Short identifiers for pre-configured process model repositories
   - File uploads (future enhancement)

2. **Import Methods**
   - Direct input of URL or identifier via UI
   - API endpoint for programmatic importing
   - Command-line interface support

3. **User Experience**
   - Simple input field for URL or identifier
   - Preview of process model content before import
   - Configuration options during import (renaming, location selection)
   - Clear feedback on import success/failure

### Import Process

1. **Identification**
   - Support for full URLs to process model repositories
   - Short identifier system for commonly used process models
   - Resolution system to convert identifiers to actual source locations

2. **Retrieval**
   - Fetch process model files from external sources
   - Support for various authentication methods (for future private repository access)
   - Handling of different repository structures

3. **Validation**
   - Verify the integrity and structure of imported process models
   - Check for required files and valid BPMN/DMN content
   - Ensure compatibility with the system

4. **Integration**
   - Place imported process models in appropriate location in the system
   - Register process models with the system
   - Handle conflicts with existing process models

## Technical Design

### Short Identifier System

The system will support two types of identifiers:
1. **Full URLs**: Direct references to process model repositories
   - Example: `https://github.com/organization/repo/path/to/process-model`
   - Example: `https://process-model-hub.example.com/models/approval-workflow`

2. **Short Identifiers**: Human-friendly, easy-to-type references
   - Format: `[namespace]/[name]`
   - Example: `common/approval-process`
   - Example: `hr/onboarding-workflow`

A resolution service will map short identifiers to actual repository locations, using a configurable registry of known sources.

### Architecture Components

#### ImportService

The `ImportService` will be responsible for:
- Resolving identifiers to repository locations
- Retrieving process model files from external sources
- Validating imported process models
- Handling the import process

#### IdentifierResolutionService

This service will:
- Map short identifiers to actual repository locations
- Manage a registry of known process model sources
- Allow for custom source registrations

#### ProcessModelRepositoryConnector

This component will:
- Connect to various repository types (Git, HTTP, etc.)
- Handle authentication for repository access
- Retrieve process model files

#### ImportController

The API controller will provide endpoints for:
- Importing process models via URL or identifier
- Checking the availability and validity of external process models
- Managing the registry of process model sources

### Security Considerations

1. **Source Validation**
   - Whitelist of allowed domains for external sources
   - Validation of repository content before import

2. **Access Control**
   - Permissions required for importing process models
   - Configurable restrictions on import sources

3. **Content Scanning**
   - Basic validation of process model content
   - Protection against malicious content

## User Interface

### Import Dialog

1. **Input Methods**
   - Text field for URL or identifier input
   - Dropdown of recently used or featured process models

2. **Preview Section**
   - Display of process model metadata
   - Preview of process model diagram (when available)
   - List of files included in the process model

3. **Configuration Options**
   - Name for the imported process model
   - Target location in the system
   - Additional metadata

### Import Process Flow

1. User enters URL or identifier
2. System resolves the identifier and retrieves metadata
3. User reviews the preview and adjusts configuration
4. User confirms the import
5. System performs the import and provides feedback

## Implementation Phases

### Phase 1: Basic URL Import (COMPLETED)

- Support for direct GitHub URLs
- Basic validation of imported content
- Simple UI for URL input
- Import into user's workspace

#### Implementation Details

The Phase 1 implementation includes:

1. Frontend components:
   - `ProcessModelImportDialog.tsx`: Dialog for entering and validating GitHub URLs
   - `ProcessModelImportButton.tsx`: Button for launching the import dialog

2. Backend components:
   - `process_model_import_controller.py`: API endpoint for processing import requests
   - `process_model_import_service.py`: Service for fetching and processing GitHub repository content

3. API contract:
   - Endpoint: `/process-model-import/{modified_process_group_id}`
   - Method: POST
   - Request body: `{ "repository_url": "https://github.com/org/repo/tree/branch/path" }`
   - Response: `{ "process_model": {...}, "import_source": "url" }`

4. Error Handling:
   - Invalid URLs are validated in the frontend before submission
   - Missing or malformed URLs return a 400 Bad Request
   - Repository not found returns a 404 Not Found
   - Invalid process models return a 400 Bad Request with details

5. Testing:
   - Backend tests in `test_process_model_import_controller.py` cover successful import, missing URL, and invalid process group
   - Frontend validation checks GitHub URL format

### Phase 2: Short Identifier System

- Implementation of identifier resolution service
- Registry of common process model sources
- UI enhancements for identifier input

### Phase 3: Advanced Features

- Support for private repositories (with authentication)
- Versioned imports
- Dependency management for process models
- Publishing imported models to internal registry

## Future Enhancements

1. **Process Model Hub**
   - Dedicated application for hosting sharable process models
   - Rating and review system for community models
   - Categories and tags for discoverability

2. **Version Control Integration**
   - Track source and version of imported models
   - Update notifications for new versions
   - Diff view for comparing versions

3. **Collaboration Features**
   - Fork and modify imported process models
   - Contribute improvements back to source
   - Access control for shared models

## Questions and Considerations

1. **Source Trust**: How to ensure the security and quality of imported process models?
2. **Versioning**: How to handle updates to imported process models?
3. **Naming Conflicts**: How to resolve conflicts with existing process models?
4. **Dependencies**: How to manage dependencies between process models?
5. **Private Sources**: How to authenticate with private repositories?

## Conclusion

The Process Model Import feature will significantly enhance the user experience by allowing easy reuse of existing process models. By implementing this feature in phases, we can deliver immediate value while building toward a comprehensive solution that supports various import scenarios and use cases.