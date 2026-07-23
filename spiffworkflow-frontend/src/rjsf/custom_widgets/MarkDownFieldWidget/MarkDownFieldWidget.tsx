import MDEditor from '@uiw/react-md-editor';
import { Box, FormHelperText, useTheme } from '@mui/material';
import React, { useCallback } from 'react';

interface WidgetArgs {
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
}: WidgetArgs) {
  const isDark = useTheme().palette.mode === 'dark';
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

  // TODO: highlight the MDEditor in some way - we are only showing red text atm.
  return (
    <div className="with-half-rem-top-margin">
      <Box data-invalid={invalid} sx={{ display: 'inline' }}>
        <div data-color-mode={isDark ? 'dark' : 'light'} id={id}>
          <MDEditor
            height={500}
            highlightEnable={false}
            value={value}
            onChange={onChangeLocal}
            autoFocus={autofocus}
          />
        </div>
      </Box>
      <FormHelperText id={`${id}-error-msg`} error={invalid}>
        {errorMessageForField}
      </FormHelperText>
      {invalid ? null : (
        <FormHelperText id="root-helper-text">{helperText}</FormHelperText>
      )}
    </div>
  );
}
