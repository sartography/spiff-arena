import React from 'react';
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
    rawErrors
  );

  // if the parent rjsf schema is not of type "object", then rjsf sends "root" through as the id.
  // this creates issues with the carbon checkbox where it will not accept any clicks to the checkbox
  // so add fuzz to the id to ensure it is unique.
  // https://github.com/rjsf-team/react-jsonschema-form/issues/1824
  const uniqueId = makeid(10);

  return (
    <Checkbox
      id={uniqueId}
      name={uniqueId}
      checked={typeof value === 'undefined' ? false : Boolean(value)}
      disabled={disabled || readonly}
      title={commonAttributes.tooltipText}
      autoFocus={autofocus}
      invalid={commonAttributes.invalid}
      invalidText={commonAttributes.errorMessageForField}
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
