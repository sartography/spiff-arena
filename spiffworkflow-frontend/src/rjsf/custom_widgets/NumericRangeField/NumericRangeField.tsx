import {
  descriptionId,
  FieldProps,
  getTemplate,
  getUiOptions,
} from '@rjsf/utils';
import { TextInput } from '@carbon/react';
import { getCommonAttributes } from '../../helpers';

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
  errorSchema = {},
  ...args
}: FieldProps) {
  const identifierToUse = Object.keys(
    schema.properties || { numericRange: {} }
  )[0];

  // console.log('errorSchema', errorSchema);

  const additionalErrors: any = rawErrors;
  // if (identifierToUse in errorSchema) {
  //   if (errorSchema[identifierToUse]?.min?.__errors) {
  //     additionalErrors = additionalErrors.concat(
  //       errorSchema[identifierToUse]?.min?.__errors || []
  //     );
  //   }
  //   if (errorSchema[identifierToUse]?.max?.__errors) {
  //     additionalErrors = additionalErrors.concat(
  //       errorSchema[identifierToUse]?.max?.__errors || []
  //     );
  //   }
  // }
  console.log('additionalErrors', additionalErrors);
  const commonAttributes = getCommonAttributes(
    label,
    schema,
    uiSchema,
    additionalErrors
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
      return numberString.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }
    return '0';
  };

  const parseNumberString = (numberString: string) =>
    Number(numberString.replace(/,/g, ''));

  // create two number inputs for min and max compensation
  const { min, max } = formData
    ? formData[identifierToUse]
    : { min: 0, max: 0 };

  const maxNumber = 999_999_999_999;

  const onChangeLocal = (nameToChange: any, event: any) => {
    event.preventDefault();
    const numberValue = parseNumberString(event.target.value);
    if (numberValue > maxNumber) {
      return;
    }
    if (!disabled && !readonly) {
      if (nameToChange === 'min' && numberValue > max) {
        onChange({
          ...(formData || {}),
          [identifierToUse]: {
            min: numberValue,
            max: numberValue,
          },
        });
      } else {
        onChange({
          ...(formData || {}),
          [identifierToUse]: {
            ...{ max, min },
            [nameToChange]: numberValue,
          },
        });
      }
    }
  };

  // console.log('commonAttributes', commonAttributes);

  return (
    <div className="numeric--range-field-wrapper">
      <div className="numeric--range-field-label">
        <h5>{commonAttributes.label}</h5>
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
          labelText={`Minimum ${schema.title || ''}`}
          disabled={disabled}
          readonly={readonly}
          value={formatNumberString(min)}
          onChange={(values: any) => {
            onChangeLocal('min', values);
          }}
          defaultValue="0"
          autofocus={autofocus}
        />
        <TextInput
          id={`${id}-max`}
          labelText={`Maximum ${schema.title || ''}`}
          disabled={disabled}
          readonly={readonly}
          value={formatNumberString(max)}
          onChange={(values: any) => onChangeLocal('max', values)}
          defaultValue="0"
        />
      </div>
      {commonAttributes.errorMessageForField && (
        <div className={`${id}-error`}>
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
