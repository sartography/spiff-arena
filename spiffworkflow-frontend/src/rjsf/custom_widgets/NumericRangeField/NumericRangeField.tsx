import {
  descriptionId,
  FieldProps,
  getTemplate,
  getUiOptions,
} from '@rjsf/utils';
import { TextInput } from '@carbon/react';
import React from 'react';
import { getCommonAttributes } from '../../helpers';

// Example jsonSchema - NOTE: the "min" and "max" properties are special names and must be used:
//    compensation":{
//      "title": "Compensation (yearly), USD",
//      "type": "object",
//      "minimum": 0,
//      "maximum": 999999999999,
//      "properties": {
//        "min": {
//          "type": "number"
//        },
//        "max": {
//          "type": "number"
//        }
//      }
//    }
//
//  Example uiSchema:
//    "compensation": {
//      "ui:field": "numeric-range",
//    }

// eslint-disable-next-line sonarjs/cognitive-complexity
export default function NumericRangeField({
  id,
  schema,
  uiSchema,
  idSchema,
  disabled,
  readonly,
  onChange,
  autofocus,
  label,
  rawErrors = [],
  formData,
  registry,
  required,
}: FieldProps) {
  const commonAttributes = getCommonAttributes(
    label,
    schema,
    uiSchema,
    rawErrors
  );

  const description = schema?.description || uiSchema?.['ui:description'];

  const uiOptions = getUiOptions(uiSchema || {});
  const DescriptionFieldTemplate = getTemplate(
    'DescriptionFieldTemplate',
    registry,
    uiOptions
  );

  const formatNumberString = (numberString: string): string => {
    // this function will change the number string to a number with commas
    // and a decimal point if needed. For example, 1000 will become 1,000
    // or 1000.5 will become 1,000.5

    if (numberString) {
      const parts = numberString.split('.');
      const integerPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
      return parts.length > 1 ? `${integerPart}.${parts[1]}` : integerPart;
    }
    return '';
  };

  const parseNumberString = (numberString: string) => {
    if (
      (numberString === '-' && numberString.length === 1) ||
      numberString.endsWith('.')
    ) {
      return null;
    }
    return Number(numberString.replace(/,/g, ''));
  };

  if (schema.minimum === undefined || schema.maximum === undefined) {
    throw new Error('minimum and maximum not defined');
  }
  const minNumber = schema.minimum;
  const maxNumber = schema.maximum;
  let min = formData?.min || null;
  const [minValue, setMinValue] = React.useState(min?.toString() || '');
  let max = formData?.max || null;
  const [maxValue, setMaxValue] = React.useState(max?.toString() || '');

  // the text input eventually breaks when the number gets too big.
  // we are not sure what the cut off really is but seems unlikely
  // people will need to go this high.

  const onChangeLocal = (nameToChange: any, event: any) => {
    event.preventDefault();
    let numberValue = parseNumberString(event.target.value);
    if (numberValue === null || (numberValue === 0 && required)) {
      const updatedFormData = { ...formData, [nameToChange]: null };
      onChange(updatedFormData);
      return;
    }
    if (nameToChange === 'min') {
      if (
        numberValue !== null &&
        minNumber !== undefined &&
        maxNumber !== undefined &&
        (numberValue < minNumber ||
          numberValue > maxNumber ||
          numberValue > max)
      ) {
        numberValue = null;
      } else {
        min = numberValue;
        let currentMax = parseNumberString(maxValue);
        if (
          currentMax !== null &&
          maxNumber !== undefined &&
          currentMax >= min &&
          currentMax <= maxNumber
        ) {
          max = currentMax;
        } else {
          max = null;
        }
      }
      setMinValue(formatNumberString(numberValue?.toString() || ''));
    }
    if (nameToChange === 'max') {
      if (
        numberValue !== null &&
        minNumber !== undefined &&
        maxNumber !== undefined &&
        (numberValue > maxNumber ||
          numberValue < minNumber ||
          numberValue < min)
      ) {
        numberValue = null;
      } else {
        max = numberValue;
        let currentMin = parseNumberString(minValue);
        if (
          currentMin !== null &&
          currentMin <= max &&
          minNumber !== undefined &&
          currentMin >= minNumber
        ) {
          min = currentMin;
        } else {
          min = null;
        }
      }
      setMaxValue(formatNumberString(numberValue?.toString() || ''));
    }
    const existingFormData = formData || {};
    if (!disabled && !readonly) {
      onChange({
        ...(formData || {}),
        ...{ max, min },
        [nameToChange]: numberValue,
      });
    }
    console.log('min', min, 'max', max);
    console.log('formData.min', formData?.min);
    console.log('formData.max', formData?.max);
  };

  return (
    <div className="numeric--range-field-wrapper">
      <div className="numeric--range-field-label">
        <h5>
          {required ? `${commonAttributes.label} *` : commonAttributes.label}
        </h5>
        {description && (
          <div className="markdown-field-desc-text">
            <DescriptionFieldTemplate
              id={descriptionId(idSchema)}
              description={description}
              schema={schema}
              uiSchema={uiSchema}
              registry={registry}
            />
          </div>
        )}
      </div>
      <div className="numeric--range-field-inputs">
        <TextInput
          id={`${id}-min`}
          type="text"
          labelText={(schema as any).properties?.min?.title || `Minimum`}
          disabled={disabled}
          readonly={readonly}
          value={formatNumberString(minValue)}
          onChange={(event: any) => {
            onChangeLocal('min', event);
            setMinValue(event.target.value.replace(/,/g, ''));
          }}
          invalid={commonAttributes.invalid}
          helperText={`Min: ${formatNumberString(minNumber?.toString() || '')}`}
          autofocus={autofocus}
        />
        <TextInput
          id={`${id}-max`}
          type="text"
          labelText={(schema as any).properties?.max?.title || `Maximum`}
          disabled={disabled}
          readonly={readonly}
          value={formatNumberString(maxValue)}
          onChange={(event: any) => {
            onChangeLocal('max', event);
            setMaxValue(event.target.value.replace(/,/g, ''));
          }}
          invalid={commonAttributes.invalid}
          helperText={`Max: ${formatNumberString(maxNumber?.toString() || '')}`}
        />
      </div>
      {commonAttributes.errorMessageForField && (
        <div className="error-message">
          {commonAttributes.errorMessageForField}
        </div>
      )}
      {commonAttributes.helperText && (
        <p className="numeric--range-field-help-text">
          {commonAttributes.helperText}
        </p>
      )}
    </div>
  );
}
