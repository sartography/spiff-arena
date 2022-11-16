import React from 'react';
// @ts-ignore
import { RadioButtonGroup, RadioButton } from '@carbon/react';
import { WidgetProps } from '@rjsf/utils';

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
}: WidgetProps) {
  const { enumOptions, enumDisabled } = options;

  const localOnChange = (_: any, value: any) =>
    onChange(schema.type == 'boolean' ? value !== 'false' : value);
  const _onBlur = ({ target: { value } }: React.FocusEvent<HTMLInputElement>) =>
    onBlur(id, value);
  const _onFocus = ({
    target: { value },
  }: React.FocusEvent<HTMLInputElement>) => onFocus(id, value);

  const row = options ? options.inline : false;

  return (
    <RadioButtonGroup
      orientation="vertical"
      id={id}
      name={id}
      value={`${value}`}
      row={row as boolean}
      legendText={label || schema.title}
      onChange={localOnChange}
      onBlur={_onBlur}
      onFocus={_onFocus}
    >
      {Array.isArray(enumOptions) &&
        enumOptions.map((option) => {
          const itemDisabled =
            Array.isArray(enumDisabled) &&
            enumDisabled.indexOf(option.value) !== -1;
          return (
            <RadioButton
              labelText={`${option.label}`}
              value={`${option.value}`}
              id={`${id}-${option.value}`}
              key={option.value}
              disabled={disabled || itemDisabled || readonly}
            />
          );
        })}
    </RadioButtonGroup>
  );
}

export default RadioWidget;
