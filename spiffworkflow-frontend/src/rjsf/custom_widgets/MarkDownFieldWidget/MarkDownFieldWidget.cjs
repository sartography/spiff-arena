'use strict';

const React = require('react');
const { useCallback } = React;
const MDEditor = require('@uiw/react-md-editor');

/**
 * @typedef {Object} WidgetArgs
 * @property {string} id
 * @property {any} value
 * @property {any} [schema]
 * @property {any} [uiSchema]
 * @property {boolean} [disabled]
 * @property {boolean} [readonly]
 * @property {any} [rawErrors]
 * @property {any} [onChange]
 * @property {any} [autofocus]
 * @property {string} [label]
 */

/**
 * @param {WidgetArgs} props
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
  let invalid = false;
  let errorMessageForField = null;

  let labelToUse = label;
  if (uiSchema && uiSchema['ui:title']) {
    labelToUse = uiSchema['ui:title'];
  } else if (schema && schema.title) {
    labelToUse = schema.title;
  }

  const onChangeLocal = useCallback(
    function(newValue) {
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
    if ('validationErrorMessage' in schema) {
      errorMessageForField = schema.validationErrorMessage;
    } else {
      errorMessageForField = `${(labelToUse || '').replace(/\*$/, '')} ${
        rawErrors[0]
      }`;
    }
  }

  // cds-- items come from carbon and how it displays helper text and errors.
  // carbon also removes helper text when error so doing that here as well.
  // TODO: highlight the MDEditor in some way - we are only showing red text atm.
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
        })
      )
    ),
    React.createElement(
      'div',
      { id: `${id}-error-msg`, className: 'cds--form-requirement' },
      errorMessageForField
    ),
    invalid
      ? null
      : React.createElement(
          'div',
          { id: 'root-helper-text', className: 'cds--form__helper-text' },
          helperText
        )
  );
}

module.exports = MarkDownFieldWidget;