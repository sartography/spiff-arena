import {
  descriptionId,
  FieldProps,
  getTemplate,
  getUiOptions,
} from '@rjsf/utils';
import { TextInput } from '@carbon/react';
import { getCommonAttributes } from '../../helpers';
import React from 'react';

// Example jsonSchema - NOTE: the "min" and "max" properties are special names and must be used:
//    compensation":{
//      "title": "Compensation (yearly), USD",
//      "type": "object",
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
    if (numberString) {
      if (numberString.includes('.')) {
        return numberString
          .toString()
          .replace(/\B(?=(\d{3}?)+(?!\d).[^\.])/g, ',');
      } else {
        return numberString.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
      }
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

  // create two number inputs for min and max compensation
  let min = formData?.min || null;
  const [minValue, setMinValue] = React.useState(min?.toString() || '');
  let max = formData?.max || null;
  const [maxValue, setMaxValue] = React.useState(max?.toString() || '');

  // the text input eventually breaks when the number gets too big.
  // we are not sure what the cut off really is but seems unlikely
  // people will need to go this high.
  const maxNumber = 999_999_999_999;

  const onChangeLocal = (nameToChange: any, event: any) => {
    event.preventDefault();
    const numberValue = parseNumberString(event.target.value);
    if (numberValue === null || (numberValue === 0 && required)) {
      if (nameToChange === 'min') {
        onChange({
          ...(formData || {}),
          min: null,
        });
      }
      if (nameToChange === 'max') {
        onChange({
          ...(formData || {}),
          max: null,
        });
      }
      return;
    }
    if (numberValue > maxNumber) {
      return;
    }
    if (nameToChange === 'min') {
      min = numberValue;
      setMinValue(formatNumberString(numberValue.toString()));
    }
    if (nameToChange === 'max') {
      max = numberValue;
      setMaxValue(formatNumberString(numberValue.toString()));
    }
    if (!disabled && !readonly) {
      if (nameToChange === 'min' && numberValue > max) {
        min = numberValue;
        setMinValue(numberValue.toString());
        max = numberValue;
        setMaxValue(numberValue.toString());
        onChange({
          ...(formData || {}),
          min: numberValue,
          max: numberValue,
        });
      } else {
        onChange({
          ...(formData || {}),
          ...{ max, min },
          [nameToChange]: numberValue,
        });
      }
    }
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
