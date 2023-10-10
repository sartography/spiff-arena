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

  // some rjsf validations add in labels by default so avoid showing it twice
  let errorMessageForFieldWithoutLabel = null;

  let invalid = false;
  let errorMessageForField = null;
  if (rawErrors && rawErrors.length > 0) {
    invalid = true;
    [errorMessageForFieldWithoutLabel] = rawErrors;
    if ('validationErrorMessage' in schema) {
      errorMessageForField = (schema as any).validationErrorMessage;
      errorMessageForFieldWithoutLabel = errorMessageForField;
    } else {
      errorMessageForField = `${labelToUse.replace(/\*$/, '')} ${rawErrors[0]}`;
    }
  }

  return {
    helperText,
    label: labelToUse,
    invalid,
    errorMessageForField,
    errorMessageForFieldWithoutLabel,
    labelWithRequiredIndicator,
    tooltipText,
  };
};

// https://stackoverflow.com/a/1349426/6090676
export const makeid = (length: number) => {
  let result = '';
  const characters = 'abcdefghijklmnopqrstuvwxyz0123456789';
  const charactersLength = characters.length;
  for (let i = 0; i < length; i += 1) {
    result += characters.charAt(Math.floor(Math.random() * charactersLength));
  }
  return result;
};
