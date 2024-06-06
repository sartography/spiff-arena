import React, { FocusEvent, useCallback } from 'react';
// @ts-ignore
import { TextArea } from '@carbon/react';
import { useDebouncedCallback } from 'use-debounce';
import {
  FormContextType,
  RJSFSchema,
  StrictRJSFSchema,
  WidgetProps,
} from '@rjsf/utils';
import { getCommonAttributes } from '../../helpers';

/** The `TextareaWidget` is a widget for rendering input fields as textarea.
 *
 * @param props - The `WidgetProps` for this component
 */
function TextareaWidget<
  T = any,
  S extends StrictRJSFSchema = RJSFSchema,
  F extends FormContextType = any,
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
    [onChange, options.emptyValue],
  );

  const handleBlur = useCallback(
    ({ target: { value } }: FocusEvent<HTMLTextAreaElement>) =>
      onBlur(id, value),
    [onBlur, id],
  );

  const handleFocus = useCallback(
    ({ target: { value } }: FocusEvent<HTMLTextAreaElement>) =>
      onFocus(id, value),
    [id, onFocus],
  );

  // this helps with performance for the select widget with rsjf 5.1+.
  // otherwise if the form has an enum with a corresponding oneOf, after choosing
  // an option in the dropdown, the text area slows way down.
  const addDebouncedOnChangeText = useDebouncedCallback(
    (fullObject: React.ChangeEvent<HTMLTextAreaElement>) => {
      handleChange(fullObject);
    },
    // delay in ms
    100,
  );

  const commonAttributes = getCommonAttributes(
    label,
    schema,
    uiSchema,
    rawErrors,
  );

  let enableCounter = false;
  let maxCount = undefined;
  if (options && options.counter) {
    enableCounter = true;
    if (schema && schema.maxLength) {
      maxCount = schema.maxLength;
    } else {
      throw new Error(
        `Counter was requested but no maxLength given on the ${label}`,
      );
    }
  }

  return (
    <TextArea
      id={id}
      name={id}
      className="text-input"
      helperText={commonAttributes.helperText}
      defaultValue={value || ''}
      labelText=""
      placeholder={placeholder}
      required={required}
      disabled={disabled}
      readOnly={readonly}
      autoFocus={autofocus}
      rows={options.rows}
      onBlur={handleBlur}
      onFocus={handleFocus}
      onChange={addDebouncedOnChangeText}
      invalid={commonAttributes.invalid}
      invalidText={commonAttributes.errorMessageForField}
      enableCounter={enableCounter}
      maxCount={maxCount}
    />
  );
}

TextareaWidget.defaultProps = {
  autofocus: false,
  options: {},
};

export default TextareaWidget;
