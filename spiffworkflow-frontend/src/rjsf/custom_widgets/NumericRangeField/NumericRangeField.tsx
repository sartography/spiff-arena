import {
  descriptionId,
  FieldProps,
  getTemplate,
  getUiOptions,
} from '@rjsf/utils';
import React from 'react';
import { TextInput } from '@carbon/react';
import { getCommonAttributes } from '../../helpers';
import { matchNumberRegex } from '../../../helpers';

// Example jsonSchema - NOTE: the "min" and "max" properties are special names and must be used:
//    "compensation":{
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
//      "ui:field": "numeric-range"
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
    rawErrors,
  );

  const description = schema?.description || uiSchema?.['ui:description'];

  const uiOptions = getUiOptions(uiSchema || {});
  const DescriptionFieldTemplate = getTemplate(
    'DescriptionFieldTemplate',
    registry,
    uiOptions,
  );

  const formatNumberString = (numberString: string): string => {
    // this function will change the number string to a number with commas
    // and a decimal point if needed. For example, 1000 will become 1,000
    // or 1000.5 will become 1,000.5

    // if it does not look like a number then just return it
    if (!numberString.match(matchNumberRegex)) {
      return numberString;
    }

    const numberStringNoCommas = numberString.replace(/,/g, '');

    if (numberStringNoCommas) {
      const parts = numberStringNoCommas.split('.');
      const integerPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
      return parts.length > 1 ? `${integerPart}.${parts[1]}` : integerPart;
    }
    return '';
  };

  const parseNumberString = (numberString: string) => {
    if (!numberString.match(matchNumberRegex)) {
      return numberString;
    }
    if (
      (numberString === '-' && numberString.length === 1) ||
      numberString.endsWith('.')
    ) {
      return null;
    }
    return Number(numberString.replace(/,/g, ''));
  };

  const minNumber = schema.minimum;
  const maxNumber = schema.maximum;
  const min = formData?.min;
  const [minValue, setMinValue] = React.useState(min?.toString() || '');
  const max = formData?.max;
  const [maxValue, setMaxValue] = React.useState(max?.toString() || '');

  // the text input eventually breaks when the number gets too big.
  // we are not sure what the cut off really is but seems unlikely
  // people will need to go this high.

  const onChangeLocal = (nameToChange: any, event: any) => {
    event.preventDefault();
    const numberValue = parseNumberString(event.target.value);
    // Validate and update the numeric range based on user input
    if (nameToChange === 'min') {
      setMinValue(formatNumberString(numberValue?.toString() || ''));
    }
    if (nameToChange === 'max') {
      setMaxValue(formatNumberString(numberValue?.toString() || ''));
    }
    if (!disabled && !readonly) {
      onChange({
        ...(formData || {}),
        ...{ max, min },
        [nameToChange]: numberValue,
      });
    }
  };

  let minHelperText = '';
  let maxHelperText = '';
  if (minNumber !== undefined || maxNumber !== undefined) {
    minHelperText = `Min: ${
      formatNumberString(minNumber?.toString() || '') || '-∞'
    }`;
    maxHelperText = `Max: ${
      formatNumberString(maxNumber?.toString() || '') || '∞'
    }`;
  }

  return (
    <div className="numeric--range-field-wrapper">
      <div>
        <h5>
          {required
            ? commonAttributes.labelWithRequiredIndicator
            : commonAttributes.label}
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
            setMinValue(event.target.value);
          }}
          invalid={commonAttributes.invalid}
          invalidText={minHelperText}
          helperText={minHelperText}
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
            setMaxValue(event.target.value);
          }}
          invalid={commonAttributes.invalid}
          invalidText={maxHelperText}
          helperText={maxHelperText}
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
