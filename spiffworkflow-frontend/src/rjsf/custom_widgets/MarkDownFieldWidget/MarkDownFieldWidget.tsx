/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable unused-imports/no-unused-vars */
import MDEditor from '@uiw/react-md-editor';
import React, { useCallback } from 'react';

interface widgetArgs {
  id: string;
  value: any;
  schema?: any;
  uiSchema?: any;
  disabled?: boolean;
  readonly?: boolean;
  rawErrors?: any;
  onChange?: any;
  autofocus?: any;
  label?: string;
}

// eslint-disable-next-line sonarjs/cognitive-complexity
export default function MarkDownFieldWidget({
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
}: widgetArgs) {
  let invalid = false;
  let errorMessageForField = null;

  let labelToUse = label;
  if (uiSchema && uiSchema['ui:title']) {
    labelToUse = uiSchema['ui:title'];
  } else if (schema && schema.title) {
    labelToUse = schema.title;
  }

  const onChangeLocal = useCallback(
    (newValue: any) => {
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
      errorMessageForField = (schema as any).validationErrorMessage;
    } else {
      errorMessageForField = `${(labelToUse || '').replace(/\*$/, '')} ${
        rawErrors[0]
      }`;
    }
  }

  // cds-- items come from carbon and how it displays helper text and errors.
  // carbon also removes helper text when error so doing that here as well.
  // TODO: highlight the MDEditor in some way - we are only showing red text atm.
  return (
    <div className="with-half-rem-top-margin">
      <div
        className="cds--text-input__field-wrapper"
        data-invalid={invalid}
        style={{ display: 'inline' }}
      >
        <div data-color-mode="light" id={id}>
          <MDEditor
            height={500}
            highlightEnable={false}
            value={value}
            onChange={onChangeLocal}
            autoFocus={autofocus}
          />
        </div>
      </div>
      <div id={`${id}-error-msg`} className="cds--form-requirement">
        {errorMessageForField}
      </div>
      {invalid ? null : (
        <div id="root-helper-text" className="cds--form__helper-text">
          {helperText}
        </div>
      )}
    </div>
  );
}
