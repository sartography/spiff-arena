'use strict';

const React = require('react');
const { useCallback } = React;

/**
 * NOTE: This widget requires MDEditor from '@uiw/react-md-editor'
 * You may need to add this to the ALLOWED_IMPORTS in WidgetSandbox.tsx
 *
 * This is a sandbox-compatible version of the MarkDownFieldWidget
 */

/**
 * A Markdown field widget that uses @uiw/react-md-editor
 * @param {Object} props - The widget properties
 * @param {string} props.id - The id of the field
 * @param {any} props.value - The current value
 * @param {Object} [props.schema] - The JSON schema for the field
 * @param {Object} [props.uiSchema] - The UI schema for the field
 * @param {boolean} [props.disabled] - Whether the field is disabled
 * @param {boolean} [props.readonly] - Whether the field is read-only
 * @param {Array} [props.rawErrors] - The validation errors
 * @param {Function} props.onChange - The function to call when the value changes
 * @param {boolean} [props.autofocus] - Whether the field should be autofocused
 * @param {string} [props.label] - The field label
 * @returns {React.ReactElement} The rendered widget
 */
function MarkDownFieldWidget({
  id,
  value,
  schema,
  uiSchema,
  disabled,
  readonly,
  onChange,
  autofocus,
  label,
  rawErrors = [],
}) {
  // Attempt to dynamically import MDEditor
  let MDEditor;
  try {
    // If MDEditor isn't available, we'll try to provide a fallback
    // This is for sandbox compatibility
    MDEditor = require('@uiw/react-md-editor');
    if (!MDEditor) {
      throw new Error('MDEditor not available');
    }
  } catch (error) {
    console.warn('MDEditor not available, using textarea fallback');
    // Fallback to a simple textarea if MDEditor is not available
    return React.createElement(
      'div',
      { className: 'markdown-field-fallback' },
      React.createElement('textarea', {
        id: id,
        value: value || '',
        disabled: disabled || readonly,
        onChange: (e) => onChange(e.target.value),
        autoFocus: autofocus,
        style: {
          width: '100%',
          minHeight: '200px',
          padding: '8px',
          fontFamily: 'monospace',
        },
      }),
      rawErrors && rawErrors.length > 0
        ? React.createElement(
            'div',
            {
              style: { color: 'red', marginTop: '4px' },
              id: `${id}-error-msg`,
            },
            rawErrors[0],
          )
        : null,
    );
  }

  let invalid = false;
  let errorMessageForField = null;

  let labelToUse = label;
  if (uiSchema && uiSchema['ui:title']) {
    labelToUse = uiSchema['ui:title'];
  } else if (schema && schema.title) {
    labelToUse = schema.title;
  }

  const onChangeLocal = useCallback(
    function (newValue) {
      if (!disabled && !readonly) {
        onChange(newValue);
      }
    },
    [onChange, disabled, readonly],
  );

  let helperText = null;
  if (uiSchema && uiSchema['ui:help']) {
    helperText = uiSchema['ui:help'];
  }

  if (!invalid && rawErrors && rawErrors.length > 0) {
    invalid = true;
    if (schema && 'validationErrorMessage' in schema) {
      errorMessageForField = schema.validationErrorMessage;
    } else {
      errorMessageForField = `${(labelToUse || '').replace(/\*$/, '')} ${
        rawErrors[0]
      }`;
    }
  }

  // cds-- items come from carbon and how it displays helper text and errors.
  // carbon also removes helper text when error so doing that here as well.
  return React.createElement(
    'div',
    { className: 'with-half-rem-top-margin' },
    React.createElement(
      'div',
      {
        className: 'cds--text-input__field-wrapper',
        'data-invalid': invalid,
        style: { display: 'inline' },
      },
      React.createElement(
        'div',
        { 'data-color-mode': 'light', id: id },
        React.createElement(MDEditor, {
          height: 500,
          highlightEnable: false,
          value: value,
          onChange: onChangeLocal,
          autoFocus: autofocus,
        }),
      ),
    ),
    React.createElement(
      'div',
      { id: `${id}-error-msg`, className: 'cds--form-requirement' },
      errorMessageForField,
    ),
    invalid
      ? null
      : React.createElement(
          'div',
          { id: 'root-helper-text', className: 'cds--form__helper-text' },
          helperText,
        ),
  );
}

// Export for sandbox compatibility
module.exports = MarkDownFieldWidget;

