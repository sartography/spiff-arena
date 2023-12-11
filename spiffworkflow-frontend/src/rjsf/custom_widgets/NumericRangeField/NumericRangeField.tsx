import { useState, useEffect } from 'react';
import { FieldProps } from '@rjsf/utils';
import { TextInput } from '@carbon/react';
import { getCommonAttributes } from '../../helpers';

export default function NumericRangeField({
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
  formData,
}: FieldProps) {
  const commonAttributes = getCommonAttributes(
    label,
    schema,
    uiSchema,
    rawErrors
  );

  let invalid = false;
  let errorMessageForField = null;

  let labelToUse = label;
  if (uiSchema && uiSchema['ui:title']) {
    labelToUse = uiSchema['ui:title'];
  } else if (schema && schema.title) {
    labelToUse = schema.title;
  }

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

  const identifierToUse = Object.keys(
    schema.properties || { numericRange: {} }
  )[0];

  const [state, setState] = useState(
    formData || {
      [identifierToUse]: {
        min: 0,
        max: 0,
      },
    }
  );

  const formatNumberString = (value: string): string => {
    if (value) {
      return value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }
    return '0';
  };

  const parseNumberString = (value: string) => Number(value.replace(/,/g, ''));

  const onChangeLocal = (nameToChange: any) => {
    return (event: any) => {
      event.preventDefault();
      const numberValue = parseNumberString(event.target.value);
      if (!disabled && !readonly) {
        if (
          numberValue > state[identifierToUse].max &&
          nameToChange === 'min'
        ) {
          setState({
            ...state,
            [identifierToUse]: {
              min: state[identifierToUse].max,
              max: numberValue,
            },
          });
          onChange({
            ...state,
            [identifierToUse]: {
              min: state[identifierToUse].max,
              max: numberValue,
            },
          });
        } else if (
          numberValue < state[identifierToUse].min &&
          nameToChange === 'max'
        ) {
          setState({
            ...state,
            [identifierToUse]: {
              max: state[identifierToUse].min,
              min: numberValue,
            },
          });
          onChange({
            ...state,
            [identifierToUse]: {
              max: state[identifierToUse].min,
              min: numberValue,
            },
          });
        } else {
          setState({
            ...state,
            [identifierToUse]: {
              ...state[identifierToUse],
              [nameToChange]: numberValue,
            },
          });
          onChange({
            ...state,
            [identifierToUse]: {
              ...state[identifierToUse],
              [nameToChange]: numberValue,
            },
          });
        }
      }
    };
  };

  const { min, max } = state[identifierToUse];
  // create two number inputs for min and max compensation

  useEffect(() => {
    console.log('formData', formData);
  }, [formData]);

  return (
    <div className="numeric--range-field-wrapper">
      <div className="numeric--range-field-label">
        <h5>{commonAttributes.label}</h5>
        {uiSchema?.['ui:description'] && (
          <p id="numeric--range-field-desc-text">
            {uiSchema?.['ui:description']}
          </p>
        )}
      </div>
      <div className="numeric--range-field-inputs">
        <TextInput
          id={`${id}-min`}
          labelText={`Minimum ${schema.title || ''}`}
          disabled={disabled}
          readonly={readonly}
          value={formatNumberString(min)}
          onChange={onChangeLocal('min')}
          defaultValue="0"
          hideSteppers
          // helperText={helperText}
        />
        {/* <div className="numeric--range-field-separator"></div> */}
        <TextInput
          id={`${id}-max`}
          labelText={`Maximum ${schema.title || ''}`}
          disabled={disabled}
          readonly={readonly}
          value={formatNumberString(max)}
          onChange={onChangeLocal('max')}
          defaultValue="0"
          hideSteppers
          // helperText={helperText}
        />
      </div>
      {errorMessageForField && (
        <div className={`${id}-error`}>{errorMessageForField}</div>
      )}
      {helperText && <p id="numeric--range-field-help-text">{helperText}</p>}
    </div>
  );
}
