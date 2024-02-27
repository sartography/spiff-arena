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
//    "name":{
//      "title": "Name",
//      "type": "string",
//      "maximum": 999999999999,
//    }
//
//  Example uiSchema:
//    "name": {
//      "ui:field": "character-counter",
//    }

// eslint-disable-next-line sonarjs/cognitive-complexity
export default function CharacterCounterField({
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

  if (schema.maximum === undefined) {
    throw new Error(
      'CharacterCounterTextField requires a "maximum" property to be specified'
    );
  }

  const text = formData || '';

  const onChangeLocal = (event: any) => {
    event.preventDefault();
    if (!disabled && !readonly) {
      onChange(event.target.value);
    }
  };

  return (
    <div className="character---counter--text-field-wrapper">
      <div className="character---counter--text-field-label">
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
      <TextInput
        id={id}
        type="text"
        disabled={disabled}
        readonly={readonly}
        value={text}
        onChange={(event: any) => {
          onChangeLocal(event);
        }}
        invalid={commonAttributes.invalid}
        enableCounter={true}
        maxCount={schema.maximum}
        autoFocus={autofocus}
      />
      {commonAttributes.errorMessageForField && (
        <div className="error-message">
          {commonAttributes.errorMessageForField}
        </div>
      )}
      {commonAttributes.helperText && (
        <p className="character---counter--text-field-help-text">
          {commonAttributes.helperText}
        </p>
      )}
    </div>
  );
}
