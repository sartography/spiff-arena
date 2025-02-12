import React, { useMemo } from 'react';
import { Checkbox } from '@carbon/react';
import { WidgetProps } from '@rjsf/utils';
import { getCommonAttributes, makeid } from '../../helpers';

function CheckboxWidget(props: WidgetProps) {
  const {
    schema,
    id,
    value,
    disabled,
    readonly,
    label,
    autofocus,
    onChange,
    onBlur,
    onFocus,
    uiSchema,
    rawErrors,
    required,
  } = props;

  const uniqueId: string = useMemo(() => {
    return makeid(10, 'checkbox-');
  }, []);

  const _onChange = (_: any, newValue: any) => {
    // if this field is required and it is not checked then change the value to undefined
    // otherwise rjsf will not flag this field as invalid
    if (required && !newValue.checked) {
      onChange(undefined);
    } else {
      onChange(newValue.checked);
    }
  };
  const _onBlur = ({
    target: { value },
  }: React.FocusEvent<HTMLButtonElement>) => onBlur(id, value);
  const _onFocus = ({
    target: { value },
  }: React.FocusEvent<HTMLButtonElement>) => onFocus(id, value);

  const commonAttributes = getCommonAttributes(
    label,
    schema,
    uiSchema,
    rawErrors,
  );

  return (
    <Checkbox
      id={uniqueId}
      name={uniqueId}
      checked={typeof value === 'undefined' ? false : Boolean(value)}
      disabled={disabled || readonly}
      title={commonAttributes.tooltipText}
      autoFocus={autofocus}
      invalid={commonAttributes.invalid}
      invalidText={commonAttributes.errorMessageForFieldWithoutLabel}
      helperText={commonAttributes.helperText}
      labelText={
        required
          ? commonAttributes.labelWithRequiredIndicator
          : commonAttributes.label
      }
      onChange={_onChange}
      onBlur={_onBlur}
      onFocus={_onFocus}
    />
  );
}

export default CheckboxWidget;
