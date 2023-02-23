import React, { FocusEvent, useCallback } from 'react';
// @ts-ignore
import { TextArea } from '@carbon/react';
import {
  FormContextType,
  RJSFSchema,
  StrictRJSFSchema,
  WidgetProps,
} from '@rjsf/utils';

/** The `TextareaWidget` is a widget for rendering input fields as textarea.
 *
 * @param props - The `WidgetProps` for this component
 */
function TextareaWidget<
  T = any,
  S extends StrictRJSFSchema = RJSFSchema,
  F extends FormContextType = any
>({
  id,
  options = {},
  value,
  required,
  disabled,
  readonly,
  autofocus = false,
  onChange,
  onBlur,
  onFocus,
  label,
  schema,
  uiSchema,
  placeholder,
  rawErrors = [],
}: WidgetProps<T, S, F>) {
  const handleChange = useCallback(
    ({ target: { value } }: React.ChangeEvent<HTMLTextAreaElement>) =>
      onChange(value === '' ? options.emptyValue : value),
    [onChange, options.emptyValue]
  );

  const handleBlur = useCallback(
    ({ target: { value } }: FocusEvent<HTMLTextAreaElement>) =>
      onBlur(id, value),
    [onBlur, id]
  );

  const handleFocus = useCallback(
    ({ target: { value } }: FocusEvent<HTMLTextAreaElement>) =>
      onFocus(id, value),
    [id, onFocus]
  );

  let labelToUse = label;
  if (uiSchema && uiSchema['ui:title']) {
    labelToUse = uiSchema['ui:title'];
  } else if (schema && schema.title) {
    labelToUse = schema.title;
  }
  if (required) {
    labelToUse = `${labelToUse}*`;
  }

  let helperText = null;
  if (uiSchema && uiSchema['ui:help']) {
    helperText = uiSchema['ui:help'];
  }

  let invalid = false;
  let errorMessageForField = null;
  if (rawErrors && rawErrors.length > 0) {
    invalid = true;
    errorMessageForField = rawErrors[0];
  }

  return (
    <TextArea
      id={id}
      name={id}
      className="text-input"
      helperText={helperText}
      value={value || ''}
      labelText=""
      placeholder={placeholder}
      required={required}
      disabled={disabled}
      readOnly={readonly}
      autoFocus={autofocus}
      rows={options.rows}
      onBlur={handleBlur}
      onFocus={handleFocus}
      onChange={handleChange}
      invalid={invalid}
      invalidText={errorMessageForField}
    />
  );
}

TextareaWidget.defaultProps = {
  autofocus: false,
  options: {},
};

export default TextareaWidget;
