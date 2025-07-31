# MarkDownFieldWidget for Widget Sandbox

This file (`MarkDownFieldWidget.sandbox.js`) is a version of the MarkDown field widget that can be run in the Widget Sandbox environment.

## Integration Notes

To properly use this widget in the sandbox:

1. The widget requires `@uiw/react-md-editor` which must be added to the `ALLOWED_IMPORTS` in `src/rjsf/sandbox/WidgetSandbox.tsx`.

2. Update the `ALLOWED_IMPORTS` in `WidgetSandbox.tsx`:

```typescript
// Add this import at the top
import MDEditor from '@uiw/react-md-editor';

// Allowed imports that extension widgets can use
const ALLOWED_IMPORTS: Record<any, any> = {
  react: React,
  '@mui/material': {}, // We'll populate this with only specific components
  '@uiw/react-md-editor': MDEditor, // Add this line
};
```

3. The widget includes a fallback to a textarea if MDEditor is not available, but the experience will be significantly better with the proper MDEditor component.

## Widget Usage

To use this widget in a form schema:

```json
{
  "type": "string",
  "title": "Description",
  "ui:widget": "markdown"
}
```

Or in your UI Schema:

```json
{
  "ui:widget": "markdown"
}
```

Remember to register the widget with an appropriate name in your widget registry.