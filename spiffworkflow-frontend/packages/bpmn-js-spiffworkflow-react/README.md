# bpmn-js-spiffworkflow-react

React components for BPMN/DMN diagram editing, built on [bpmn-js-spiffworkflow](https://github.com/sartography/bpmn-js-spiffworkflow).

## Installation

### From Git (without npm publish)

```json
{
  "dependencies": {
    "bpmn-js-spiffworkflow-react": "github:sartography/spiff-arena#main&path=spiffworkflow-frontend/packages/bpmn-js-spiffworkflow-react"
  }
}
```

### Peer Dependencies

Your app must install these dependencies:

```bash
npm install react react-dom bpmn-js bpmn-js-properties-panel bpmn-js-spiffworkflow dmn-js dmn-js-properties-panel diagram-js
```

Or add to package.json:

```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "bpmn-js": "^18.9.1",
    "bpmn-js-properties-panel": "^5.44.0",
    "bpmn-js-spiffworkflow": "github:sartography/bpmn-js-spiffworkflow#main",
    "dmn-js": "^17.4.0",
    "dmn-js-properties-panel": "^3.8.3",
    "diagram-js": "^15.4.0"
  }
}
```

## Quick Start

```tsx
import {
  BpmnEditor,
  BpmnEditorRef,
  DefaultBpmnApiService,
} from 'bpmn-js-spiffworkflow-react';
import { useRef } from 'react';

// Create an API service (or implement your own)
const apiService = new DefaultBpmnApiService({
  baseUrl: '/api/v1',
  templateBaseUrl: '/templates/',
});

function MyEditor() {
  const editorRef = useRef<BpmnEditorRef>(null);

  const handleSave = async () => {
    const xml = await editorRef.current?.getXML();
    console.log('Diagram XML:', xml);
  };

  return (
    <div>
      <button onClick={handleSave}>Save</button>
      <BpmnEditor
        ref={editorRef}
        apiService={apiService}
        modifiedProcessModelId="my:process"
        diagramType="bpmn"
        fileName="diagram.bpmn"
      />
    </div>
  );
}
```

## Naming Convention: Process Model Identifiers

This package uses a clear naming convention to distinguish between two formats of process model identifiers:

- **`processModelId`** (slash-separated): Canonical hierarchical identifier from API
  - Format: `"group/subgroup/model"`
  - Used for display and internal logic
  - Semantic meaning: hierarchical path

- **`modifiedProcessModelId`** (colon-separated): URL-safe format
  - Format: `"group:subgroup:model"`
  - Used for URL path parameters and API calls
  - Prevents routing issues with slashes in URLs

### Helper Functions

```typescript
import {
  modifyProcessIdentifierForPathParam,
  unModifyProcessIdentifierForPathParam,
} from '../helpers';

// Convert slash → colon for URLs
const urlSafe = modifyProcessIdentifierForPathParam('group/subgroup/model');
// Returns: "group:subgroup:model"

// Convert colon → slash for display/logic
const canonical = unModifyProcessIdentifierForPathParam('group:subgroup:model');
// Returns: "group/subgroup/model"
```

## Components

### BpmnEditor

The main diagram editor component supporting BPMN, DMN, and read-only viewing.

#### Props

| Prop                     | Type                            | Required | Description                                                        |
| ------------------------ | ------------------------------- | -------- | ------------------------------------------------------------------ |
| `apiService`             | `BpmnApiService`                | Yes      | API service for loading/saving diagrams                            |
| `modifiedProcessModelId` | `string`                        | Yes      | Colon-separated process model identifier (URL-safe, e.g., "a:b:c") |
| `diagramType`            | `'bpmn' \| 'dmn' \| 'readonly'` | Yes      | Type of diagram editor                                             |
| `diagramXML`             | `string \| null`                | No       | Pre-loaded diagram XML (skips API call)                            |
| `fileName`               | `string`                        | No       | File name to load from API                                         |
| `url`                    | `string`                        | No       | URL to fetch diagram from                                          |
| `tasks`                  | `BasicTask[]`                   | No       | Tasks to highlight (for readonly view)                             |
| `taskMetadataKeys`       | `TaskMetadataItem[]`            | No       | Metadata keys for task configuration                               |

#### Event Handlers

| Handler                      | Description                                  |
| ---------------------------- | -------------------------------------------- |
| `onElementClick`             | Called when a diagram element is clicked     |
| `onElementsChanged`          | Called when diagram elements are modified    |
| `onLaunchScriptEditor`       | Called when user wants to edit a script      |
| `onLaunchMarkdownEditor`     | Called when user wants to edit markdown      |
| `onLaunchBpmnEditor`         | Called when navigating to a call activity    |
| `onLaunchDmnEditor`          | Called when editing a DMN reference          |
| `onLaunchJsonSchemaEditor`   | Called when editing a JSON schema file       |
| `onLaunchMessageEditor`      | Called when editing a message                |
| `onServiceTasksRequested`    | Called when service task list is needed      |
| `onDataStoresRequested`      | Called when data store list is needed        |
| `onMessagesRequested`        | Called when message list is needed           |
| `onDmnFilesRequested`        | Called when DMN file list is needed          |
| `onJsonSchemaFilesRequested` | Called when JSON schema list is needed       |
| `onSearchProcessModels`      | Called when searching for call activities    |
| `onCallActivityOverlayClick` | Called when call activity overlay is clicked |

#### Ref Methods (BpmnEditorRef)

```tsx
interface BpmnEditorRef {
  getXML(): Promise<string>; // Get current diagram XML
  zoom(amount: number): void; // Zoom: 1=in, -1=out, 0=fit
  getModeler(): any; // Access underlying bpmn-js modeler
}
```

## API Service

You must provide an API service that implements `BpmnApiService`. You can:

1. Use `DefaultBpmnApiService` with configuration
2. Extend `DefaultBpmnApiService`
3. Implement `BpmnApiService` from scratch

### BpmnApiService Interface

```typescript
interface BpmnApiService {
  // Required
  loadDiagramFile(
    modifiedProcessModelId: string,
    fileName: string,
  ): Promise<{ file_contents: string }>;
  saveDiagramFile(
    modifiedProcessModelId: string,
    fileName: string,
    content: string,
  ): Promise<void>;
  loadDiagramTemplate(templateName: string): Promise<string>;

  // Optional - for enhanced editor features
  getServiceTasks?(): Promise<any[]>;
  getDataStores?(): Promise<any[]>;
  getMessages?(): Promise<any[]>;
  getDmnFiles?(): Promise<any[]>;
  getJsonSchemaFiles?(): Promise<any[]>;
  searchProcessModels?(query: string): Promise<any[]>;
}
```

### Using DefaultBpmnApiService

```typescript
import { DefaultBpmnApiService } from 'bpmn-js-spiffworkflow-react';

const apiService = new DefaultBpmnApiService({
  baseUrl: '/api/v1', // Base URL for API calls
  templateBaseUrl: '/static/', // Base URL for diagram templates
  headers: {
    // Custom headers (e.g., auth)
    Authorization: 'Bearer xxx',
  },
  onError: (error) => {
    // Global error handler
    console.error('API Error:', error);
  },
  onUnauthorized: () => {
    // Handle 401 responses
    window.location.href = '/login';
  },
});
```

### Custom Implementation Example

```typescript
import { BpmnApiService } from 'bpmn-js-spiffworkflow-react';

class MyApiService implements BpmnApiService {
  async loadDiagramFile(modifiedProcessModelId: string, fileName: string) {
    const response = await myHttpClient.get(
      `/models/${modifiedProcessModelId}/files/${fileName}`,
    );
    return { file_contents: response.data.content };
  }

  async saveDiagramFile(
    modifiedProcessModelId: string,
    fileName: string,
    content: string,
  ) {
    await myHttpClient.put(
      `/models/${modifiedProcessModelId}/files/${fileName}`,
      {
        content,
      },
    );
  }

  async loadDiagramTemplate(templateName: string) {
    const response = await fetch(`/templates/${templateName}`);
    return response.text();
  }
}
```

---

## Required API Endpoints

The following endpoints are used by `DefaultBpmnApiService`. Implement these in your backend or customize the API service.

### Core Endpoints (Required)

#### Load Diagram File

```http
GET /process-models/{process_model_id}/files/{file_name}
```

**Response:**

```json
{
  "file_contents": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>..."
}
```

#### Save Diagram File

```http
PUT /process-models/{process_model_id}/files/{file_name}
```

**Request Body:**

```json
{
  "file_contents": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>..."
}
```

**Response:** `200 OK` (empty or confirmation)

#### Load Diagram Template

```http
GET /{template_name}
```

Static file serving. Templates should be `.bpmn` or `.dmn` XML files.

**Required templates:**

- `new_bpmn_diagram.bpmn` - Empty BPMN diagram with `{{PROCESS_ID}}` placeholder
- `new_dmn_diagram.dmn` - Empty DMN diagram with `{{DECISION_ID}}` placeholder

**Example `new_bpmn_diagram.bpmn`:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
                  id="Definitions_1"
                  targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="{{PROCESS_ID}}" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="{{PROCESS_ID}}">
      <bpmndi:BPMNShape id="_BPMNShape_StartEvent_2" bpmnElement="StartEvent_1">
        <dc:Bounds x="179" y="79" width="36" height="36" />
      </bpmndi:BPMNShape>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
```

---

### Optional Endpoints (Enhanced Features)

These endpoints enable additional editor features. If not implemented, the corresponding features won't work but the editor will still function.

#### Get Service Tasks

Used for service task autocomplete in the properties panel.

```http
GET /service-tasks
```

**Response:**

```json
[
  {
    "id": "send-email",
    "name": "Send Email",
    "description": "Sends an email via SMTP",
    "parameters": [
      { "name": "to", "type": "string", "required": true },
      { "name": "subject", "type": "string", "required": true },
      { "name": "body", "type": "string", "required": true }
    ]
  }
]
```

#### Get Data Stores

Used for data store reference selection.

```http
GET /data-stores
```

**Response:**

```json
[
  {
    "id": "customer-db",
    "name": "Customer Database",
    "type": "database"
  }
]
```

#### Get Messages

Used for message event configuration.

```http
GET /messages
```

**Response:**

```json
[
  {
    "id": "order-received",
    "name": "Order Received",
    "correlation_properties": [{ "name": "orderId", "type": "string" }]
  }
]
```

#### Get DMN Files

Used for business rule task DMN file selection.

```http
GET /dmn-files
```

**Response:**

```json
[
  {
    "id": "pricing-rules",
    "name": "Pricing Rules",
    "file_name": "pricing.dmn"
  }
]
```

#### Get JSON Schema Files

Used for user task form selection.

```http
GET /json-schema-files
```

**Response:**

```json
[
  {
    "id": "customer-form",
    "name": "Customer Form",
    "file_name": "customer-schema.json"
  }
]
```

#### Search Process Models

Used for call activity process selection.

```http
GET /process-models?search={query}
```

**Response:**

```json
[
  {
    "id": "subprocess-approval",
    "display_name": "Approval Subprocess",
    "description": "Handles approval workflow"
  }
]
```

---

## Types

### BasicTask

Used for highlighting tasks in readonly view:

```typescript
interface BasicTask {
  id: number;
  guid?: string;
  process_instance_id?: number;
  bpmn_identifier: string; // ID of the BPMN element
  bpmn_name?: string;
  bpmn_process_direct_parent_guid?: string;
  bpmn_process_definition_identifier: string; // Process ID the task belongs to
  typename: string; // e.g., "UserTask", "ScriptTask", "CallActivity"
  state: string; // "COMPLETED", "READY", "WAITING", "STARTED", "CANCELLED", "ERROR"
  runtime_info?: Record<string, any>;
  properties_json?: Record<string, any>;
}
```

### ProcessModel

```typescript
interface ProcessModel {
  id: string;
  display_name: string;
  description?: string;
  primary_file_name?: string;
}
```

### ProcessReference

Used for showing callers of a process:

```typescript
interface ProcessReference {
  relative_location: string; // e.g., "group/subgroup/process-id"
  display_name: string;
}
```

---

## Utilities

The package exports several utility functions:

```typescript
import {
  // BPMN helpers
  getBpmnProcessIdentifiers, // Extract process IDs from diagram
  convertSvgElementToHtmlString, // Convert React SVG to HTML string
  makeid, // Generate random ID
  taskIsMultiInstanceChild, // Check if task is MI child
  checkTaskCanBeHighlighted, // Check if task can be highlighted

  // JSON Schema helpers (for User Task forms)
  extractSchemaBaseName, // "my-form-schema.json" -> "my-form"
  toValidSchemaName, // Sanitize string to valid schema name
  validateSchemaName, // Validate name, returns error or null
  getSchemaFileNames, // Get {schemaFile, uiSchemaFile, exampleDataFile}
  deriveSchemaNameFromElement, // Derive name from BPMN element
  isSchemaFile, // Check if filename is schema-related
  SCHEMA_NAME_PATTERN, // Regex for valid schema names
  SCHEMA_EXTENSIONS, // File extension constants
} from 'bpmn-js-spiffworkflow-react';
```

---

## Headless Hooks

For building custom UI around editor features, the package provides headless hooks that handle logic while letting you provide your own components.

### useJsonSchemaEditor

Manages JSON Schema file creation/editing for User Task forms.

```typescript
import { useJsonSchemaEditor } from 'bpmn-js-spiffworkflow-react';

const [state, actions] = useJsonSchemaEditor({
  open: isModalOpen,
  fileName: 'my-form-schema.json', // empty for new schema
  modifiedProcessModelId: 'my:process', // Colon-separated (URL-safe format)
  apiService: myApiService,
  element: bpmnElement, // for deriving default name
  eventBus: modelerEventBus,
  onClose: () => setModalOpen(false),
  onSave: () => showSuccess('Saved!'),
  onError: (msg) => showError(msg),
});

// state: { mode, loading, saving, baseName, schemaContent, uiSchemaContent, ... }
// actions: { setSchemaContent, save, createSchema, close, ... }
```

### useProcessSearch

Manages process search/selection for Call Activity configuration.

```typescript
import { useProcessSearch } from 'bpmn-js-spiffworkflow-react';

const [state, actions] = useProcessSearch({
  apiService: myApiService,
  onSelect: (process) => console.log('Selected:', process),
});

// state: { isOpen, processes, filteredProcesses, loading, query }
// actions: { open, close, select, setQuery, refresh }
```

---

## CSS

The package includes necessary CSS. Import in your app:

```tsx
import 'bpmn-js-spiffworkflow-react';
// or specifically:
import 'bpmn-js-spiffworkflow-react/src/styles/bpmn-js-properties-panel.css';
```

Additional CSS from bpmn-js is imported automatically.

---

## Full Example

```tsx
import React, { useRef, useState } from 'react';
import {
  BpmnEditor,
  BpmnEditorRef,
  BpmnApiService,
  BasicTask,
} from 'bpmn-js-spiffworkflow-react';

// Custom API service implementation
class MyBpmnApiService implements BpmnApiService {
  private baseUrl: string;
  private token: string;

  constructor(baseUrl: string, token: string) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  private async request(path: string, options: RequestInit = {}) {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.token}`,
        ...options.headers,
      },
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response;
  }

  async loadDiagramFile(modifiedProcessModelId: string, fileName: string) {
    const response = await this.request(
      `/models/${modifiedProcessModelId}/files/${fileName}`,
    );
    return response.json();
  }

  async saveDiagramFile(
    modifiedProcessModelId: string,
    fileName: string,
    content: string,
  ) {
    await this.request(`/models/${modifiedProcessModelId}/files/${fileName}`, {
      method: 'PUT',
      body: JSON.stringify({ file_contents: content }),
    });
  }

  async loadDiagramTemplate(templateName: string) {
    const response = await fetch(`/templates/${templateName}`);
    return response.text();
  }
}

function ProcessEditor({
  modifiedProcessModelId,
  fileName,
}: {
  modifiedProcessModelId: string;
  fileName: string;
}) {
  const editorRef = useRef<BpmnEditorRef>(null);
  const [apiService] = useState(
    () => new MyBpmnApiService('/api/v1', 'my-token'),
  );

  const handleSave = async () => {
    const xml = await editorRef.current?.getXML();
    if (xml) {
      await apiService.saveDiagramFile(modifiedProcessModelId, fileName, xml);
      alert('Saved!');
    }
  };

  const handleElementClick = (element: any, processIds: string[]) => {
    console.log('Clicked:', element.id, 'in processes:', processIds);
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '10px' }}>
        <button onClick={handleSave}>Save</button>
        <button onClick={() => editorRef.current?.zoom(1)}>Zoom In</button>
        <button onClick={() => editorRef.current?.zoom(-1)}>Zoom Out</button>
        <button onClick={() => editorRef.current?.zoom(0)}>Fit</button>
      </div>
      <div style={{ flex: 1 }}>
        <BpmnEditor
          ref={editorRef}
          apiService={apiService}
          modifiedProcessModelId={modifiedProcessModelId}
          diagramType="bpmn"
          fileName={fileName}
          onElementClick={handleElementClick}
        />
      </div>
    </div>
  );
}

// Readonly viewer with task highlighting
function ProcessViewer({ tasks }: { tasks: BasicTask[] }) {
  const editorRef = useRef<BpmnEditorRef>(null);
  const [apiService] = useState(
    () => new MyBpmnApiService('/api/v1', 'my-token'),
  );

  return (
    <BpmnEditor
      ref={editorRef}
      apiService={apiService}
      modifiedProcessModelId="my:process"
      diagramType="readonly"
      fileName="diagram.bpmn"
      tasks={tasks}
      onCallActivityOverlayClick={(task, event) => {
        console.log('Navigate to subprocess:', task);
      }}
    />
  );
}
```

---
