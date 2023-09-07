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
      onChange(newValue);
    },
    [onChange]
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

  return (
    <MDEditor
      height={500}
      highlightEnable={false}
      value={value}
      onChange={onChangeLocal}
    />
  );
}
