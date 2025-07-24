# Custom Widget Extensions for SpiffWorkflow Forms

This document explains how to create and use custom form widgets in SpiffWorkflow extensions.

## Overview

Custom widgets allow you to extend the form capabilities of SpiffWorkflow by creating specialized input components. These widgets can be used in JSON Schema Forms to enhance the user experience, provide specialized inputs, or integrate with external systems.

Custom widgets are loaded from extension process models and are securely sandboxed to prevent security issues.

## Adding a Custom Widget to Your Extension

There are two ways to add custom widgets to your extension:

### 1. Using Extension UI Schema - Widgets Section (Recommended)

Add a `widgets` array to your `extension_uischema.json` file:

```json
{
  "version": "0.2",
  "pages": { ... },
  "ux_elements": [ ... ],
  "widgets": [
    {
      "name": "my-rating-widget",
      "file": "rating_widget.js",
      "metadata": {
        "displayName": "Rating Widget",
        "description": "A widget for rating with stars",
        "version": "1.0.0",
        "author": "Your Name"
      }
    }
  ]
}
```

### 2. Using UX Elements with Widget Display Location

Alternatively, you can use the UX Elements approach:

```json
{
  "version": "0.2",
  "pages": { ... },
  "ux_elements": [
    {
      "label": "My Rating Widget",
      "page": "/my-page",
      "display_location": "widget",
      "location_specific_configs": {
        "widget_file": "rating_widget.js",
        "widget_name": "my-rating-widget",
        "widget_metadata": {
          "displayName": "Rating Widget",
          "description": "A widget for rating with stars",
          "version": "1.0.0",
          "author": "Your Name"
        }
      }
    }
  ]
}
```

## Creating a Widget File

Widget files are JavaScript (.js) files that export a React component.

**Important**: 
- Files must use CommonJS module syntax with `module.exports` (not ES6 import/export)
- Use `require()` to import React and other libraries inside your component function, not at the top level
- Use `React.createElement()` instead of JSX syntax - JSX will cause errors
- Don't include external dependencies - use only allowed libraries (React, MUI, Carbon)

Here's a basic template:

```javascript
// rating_widget.js
module.exports = {
  default: function RatingWidget(props) {
    const React = require('react');
    const mui = require('@mui/material');
    
    const { id, value, onChange, label } = props;
    
    // IMPORTANT: Use React.createElement instead of JSX
    return React.createElement(
      mui.Box,
      null,
      [
        React.createElement(mui.Typography, { key: 'label' }, label),
        React.createElement(mui.Rating, { 
          key: 'rating',
          id: id, 
          value: value || 0,
          onChange: (event, newValue) => onChange(newValue)
        })
      ]
    );
  }
};
```

## Widget Props

Your widget will receive the following props:

| Prop | Type | Description |
|------|------|-------------|
| `id` | string | Unique identifier for the field |
| `value` | any | Current value of the field |
| `onChange` | function | Function to call when value changes |
| `schema` | object | JSON schema for this field |
| `uiSchema` | object | UI schema for this field |
| `label` | string | Field label |
| `required` | boolean | Whether field is required |
| `disabled` | boolean | Whether field is disabled |
| `readonly` | boolean | Whether field is read-only |
| `rawErrors` | string[] | Validation errors |
| `options` | object | Custom options from UI schema |

## Using the Widget in Forms

Once your widget is registered, you can use it in your form UI schema:

```json
{
  "ui:widget": "my-rating-widget",
  "ui:options": {
    "customOption1": "value1",
    "customOption2": "value2"
  }
}
```

The options specified in `ui:options` will be passed to your widget in the `options` prop.

## Security Restrictions

For security reasons, widgets run in a sandboxed environment with the following restrictions:

1. **Limited Access**: Widgets can't access browser APIs like `document`, `window`, `localStorage`, etc.
2. **Allowed Imports**: Only specific React, MUI, and Carbon components can be imported.
3. **No Network Access**: Direct network requests are not allowed.
4. **No Eval**: Dynamic code evaluation is prohibited.

### Allowed Import Libraries

- `react`: Core React functionality
- `@mui/material`: Selected Material UI components
- `@carbon/react`: Selected Carbon components

## Allowed MUI Components

The following Material UI components are available:

- Button, TextField, Select, MenuItem
- FormControl, InputLabel, FormHelperText
- Checkbox, Radio, RadioGroup, FormControlLabel
- Switch, Slider, Typography, Box, Grid
- Paper, Card, CardContent, CardActions, Divider

## Allowed Carbon Components

The following Carbon components are available:

- Button, TextInput, Select, SelectItem, ComboBox
- FormGroup, Checkbox, RadioButton, RadioButtonGroup
- Toggle, Slider, Tag, InlineLoading

## Example Widgets

### 1. Simple Rating Widget

```javascript
module.exports = {
  default: function RatingWidget(props) {
    const React = require('react');
    const { useState } = React;
    const mui = require('@mui/material');
    
    const { id, value, onChange, label, required } = props;
    
    // Always use React.createElement instead of JSX
    return React.createElement(
      mui.Box,
      null,
      [
        React.createElement(mui.Typography, { key: 'label' }, label + (required ? ' *' : '')),
        React.createElement(mui.Rating, { 
          key: 'rating',
          id: id, 
          value: value || 0,
          onChange: (event, newValue) => onChange(newValue)
        })
      ]
    );
  }
};
```

### 2. Autocomplete Widget

```javascript
module.exports = {
  default: function AutocompleteWidget(props) {
    const React = require('react');
    const { useState, useEffect } = React;
    const mui = require('@mui/material');
    
    const { id, value, onChange, options, label } = props;
    const [inputValue, setInputValue] = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [loading, setLoading] = useState(false);
    
    // Mock data fetch - in a real widget you would use the options
    // to determine how to get data
    useEffect(() => {
      if (inputValue.length > 1) {
        setLoading(true);
        setTimeout(() => {
          setSuggestions([
            { id: 1, label: inputValue + '1' },
            { id: 2, label: inputValue + '2' },
            { id: 3, label: inputValue + '3' },
          ]);
          setLoading(false);
        }, 500);
      }
    }, [inputValue]);
    
    // Create the render input function without JSX
    const renderInput = function(params) {
      const endAdornment = React.createElement(
        React.Fragment,
        null,
        [
          loading && React.createElement(mui.CircularProgress, { key: 'progress', color: 'inherit', size: 20 }),
          params.InputProps.endAdornment
        ].filter(Boolean)
      );
      
      const inputProps = {
        ...params.InputProps,
        endAdornment: endAdornment
      };
      
      return React.createElement(mui.TextField, {
        ...params,
        label: label,
        InputProps: inputProps
      });
    };
    
    // Create the Autocomplete component with React.createElement
    return React.createElement(mui.Autocomplete, {
      id: id,
      value: value,
      onChange: (event, newValue) => onChange(newValue),
      inputValue: inputValue,
      onInputChange: (event, newInputValue) => setInputValue(newInputValue),
      options: suggestions,
      getOptionLabel: (option) => option?.label || '',
      loading: loading,
      renderInput: renderInput
    });
  }
};
```

## Best Practices

1. **Keep Widgets Focused**: Each widget should do one thing well.
2. **Handle Errors Gracefully**: Add error handling to avoid crashing the form.
3. **Support All Props**: Handle required, disabled, and readonly states.
4. **Show Validation**: Display rawErrors when provided.
5. **Default Values**: Always handle null/undefined values gracefully.
6. **Documentation**: Add comments to your code to explain how it works.

## Troubleshooting

If your widget doesn't appear or doesn't work as expected:

1. Check the browser console for errors
2. Verify that your widget file is properly referenced in the extension_uischema.json
3. Ensure your widget exports a default function or object
4. Check that you're not trying to use disallowed APIs
5. Verify that your UI schema correctly references the widget name

For more complex issues, look at the example widgets in `/src/rjsf/examples/` for guidance.