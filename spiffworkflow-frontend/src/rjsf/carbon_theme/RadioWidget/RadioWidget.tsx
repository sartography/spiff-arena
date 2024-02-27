import React from 'react';
import { RadioButtonGroup, RadioButton } from '@carbon/react';
import { WidgetProps } from '@rjsf/utils';
import { getCommonAttributes } from '../../helpers';

// Example uiSchema:{
//     "driving": {
//         "ui:widget": "radio",
//         "ui:options": {
//             "inline": true
//         },
//         "ui:help": "Click on Yes if you are a good driver!",
//         "ui:placeholder": "Test Place Holder",
//         "ui:layout": "column"
//     }
// }

function RadioWidget({
  id,
  schema,
  options,
  value,
  required,
  disabled,
  readonly,
  label,
  onChange,
  onBlur,
  onFocus,
  uiSchema,
  rawErrors,
}: WidgetProps) {
  const { enumOptions, enumDisabled } = options;

  const _onChange = (newValue: any, _radioButtonId: any) => {
    if (schema.type === 'boolean') {
      const v: any = newValue === 'true' || newValue === true;
      onChange(v);
    } else {
      onChange(newValue);
    }
  };

  const column = uiSchema?.['ui:layout']?.toString().toLowerCase() === 'column';
  const _onBlur = ({ target: { value } }: React.FocusEvent<HTMLInputElement>) =>
    onBlur(id, value);
  const _onFocus = ({
    target: { value },
  }: React.FocusEvent<HTMLInputElement>) => onFocus(id, value);

  const row = options ? options.inline : false;

  const commonAttributes = getCommonAttributes(
    label,
    schema,
    uiSchema,
    rawErrors
  );

  // pass values in as strings so we can support both boolean and string radio buttons
  return (
    <RadioButtonGroup
      id={id}
      name={id}
      legendText={commonAttributes.helperText}
      valueSelected={`${value}`}
      invalid={commonAttributes.invalid}
      invalidText={commonAttributes.errorMessageForFieldWithoutLabel}
      disabled={disabled || readonly}
      onChange={_onChange}
      onBlur={_onBlur}
      onFocus={_onFocus}
    >
      <div className={`radio-button-group-${column ? 'column' : 'row'}`}>
        {Array.isArray(enumOptions) &&
          enumOptions.map((option) => {
            return (
              <RadioButton
                id={`${id}-${option.value}`}
                labelText={option.label}
                value={`${option.value}`}
              />
            );
          })}
      </div>
    </RadioButtonGroup>
  );
}

export default RadioWidget;
