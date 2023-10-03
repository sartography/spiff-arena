import React from 'react';
import FormControlLabel from '@mui/material/FormControlLabel';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import { WidgetProps } from '@rjsf/utils';
import { getCommonAttributes } from '../../helpers';

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

  const _onChange = (_: any, newValue: any) => {
    if (schema.type === 'boolean') {
      const v: any = newValue === 'true' || newValue === true;
      onChange(v);
    } else {
      onChange(newValue);
    }
  };
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

  return (
    <RadioGroup
      id={id}
      name={id}
      value={`${value}`}
      row={row as boolean}
      onChange={_onChange}
      onBlur={_onBlur}
      onFocus={_onFocus}
    >
      {Array.isArray(enumOptions) &&
        enumOptions.map((option) => {
          const itemDisabled =
            Array.isArray(enumDisabled) &&
            enumDisabled.indexOf(option.value) !== -1;
          return (
            <FormControlLabel
              control={
                <Radio name={id} id={`${id}-${option.value}`} color="primary" />
              }
              label={`${option.label}`}
              value={`${option.value}`}
              key={option.value}
              disabled={disabled || itemDisabled || readonly}
            />
          );
        })}
    </RadioGroup>
  );
}

export default RadioWidget;
