const REQUIRED_FIELD_SYMBOL = '*';
export const getCommonAttributes = (
  label: string,
  schema: any,
  uiSchema: any,
  rawErrors: any
) => {
  let labelToUse = label;
  if (uiSchema && uiSchema['ui:title']) {
    labelToUse = uiSchema['ui:title'];
  } else if (schema && schema.title) {
    labelToUse = schema.title;
  }

  const labelWithRequiredIndicator = `${labelToUse}${REQUIRED_FIELD_SYMBOL}`;

  let helperText = null;
  let tooltipText = null;
  if (uiSchema) {
    if (uiSchema['ui:help']) {
      helperText = uiSchema['ui:help'];
    }
    if (uiSchema['ui:tooltip']) {
      tooltipText = uiSchema['ui:tooltip'];
    }
  }

  let invalid = false;
  let errorMessageForField = null;
  if (rawErrors && rawErrors.length > 0) {
    invalid = true;
    if ('validationErrorMessage' in schema) {
      errorMessageForField = (schema as any).validationErrorMessage;
    } else {
      errorMessageForField = `${labelToUse.replace(/\*$/, '')} ${rawErrors[0]}`;
    }
  }

  return {
    helperText,
    label: labelToUse,
    invalid,
    errorMessageForField,
    labelWithRequiredIndicator,
    tooltipText,
  };
};
