import React, { useMemo } from 'react';
import { RadioButtonGroup, RadioButton } from '@carbon/react';
import { WidgetProps } from '@rjsf/utils';
import { getCommonAttributes, makeid } from '../../helpers';

function RadioWidget({
  id,
  schema,
  options,
  value,
  disabled,
  readonly,
  label,
  onChange,
  onBlur,
  onFocus,
  uiSchema,
  rawErrors,
}: WidgetProps) {
  const { enumOptions } = options;

  const uniqueId: string = useMemo(() => {
    return makeid(10, 'radio-button-');
  }, []);

  const _onChange = (newValue: any, _radioButtonId: any) => {
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
    rawErrors,
  );

  // pass values in as strings so we can support both boolean and string radio buttons
  return (
    <RadioButtonGroup
      id={uniqueId}
      name={uniqueId}
      legendText={commonAttributes.helperText}
      valueSelected={`${value}`}
      invalid={commonAttributes.invalid}
      invalidText={commonAttributes.errorMessageForFieldWithoutLabel}
      disabled={disabled || readonly}
      onChange={_onChange}
      onBlur={_onBlur}
      onFocus={_onFocus}
      orientation={row ? 'horizontal' : 'vertical'}
      className="radio-button-group"
    >
      {Array.isArray(enumOptions) &&
        enumOptions.map((option) => {
          return (
            <RadioButton
              id={`${uniqueId}-${option.value}`}
              labelText={option.label}
              value={`${option.value}`}
            />
          );
        })}
    </RadioButtonGroup>
  );
}

export default RadioWidget;
