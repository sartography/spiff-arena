import { Select, SelectItem } from '@carbon/react';
import { WidgetProps, processSelectValue } from '@rjsf/utils';

function SelectWidget({
  schema,
  id,
  options,
  label,
  required,
  disabled,
  readonly,
  value,
  multiple,
  autofocus,
  onChange,
  onBlur,
  onFocus,
  uiSchema,
  placeholder,
  rawErrors = [],
}: WidgetProps) {
  const { enumOptions, enumDisabled } = options;

  const emptyValue = multiple ? [] : '';

  const _onChange = ({
    target: { value },
  }: React.ChangeEvent<{ name?: string; value: unknown }>) =>
    onChange(processSelectValue(schema, value, options));
  const _onBlur = ({ target: { value } }: React.FocusEvent<HTMLInputElement>) =>
    onBlur(id, processSelectValue(schema, value, options));
  const _onFocus = ({
    target: { value },
  }: React.FocusEvent<HTMLInputElement>) =>
    onFocus(id, processSelectValue(schema, value, options));

  let labelToUse = label;
  if (uiSchema && uiSchema['ui:title']) {
    labelToUse = uiSchema['ui:title'];
  } else if (schema && schema.title) {
    labelToUse = schema.title;
  }
  let helperText = null;
  if (uiSchema && uiSchema['ui:help']) {
    helperText = uiSchema['ui:help'];
  }
  if (required) {
    labelToUse = `${labelToUse}*`;
  }

  let invalid = false;
  let errorMessageForField = null;
  if (rawErrors && rawErrors.length > 0) {
    invalid = true;
    // errorMessageForField = `${labelToUse.replace(/\*$/, '')} ${rawErrors[0]}`;
    errorMessageForField = rawErrors[0];
  }

  // ok. so in safari, the select widget showed the first option, whereas in chrome it forced you to select an option.
  // this change causes chrome to also show the first option. now all browsers are consistent on our site. you no longer have to select anything.
  // setting the value prop causes it to show the first option.
  // calling onChange actually gets it set in the form data.
  if (enumOptions && enumOptions[0].value !== '') {
    enumOptions.unshift({ value: '', label: '' });
  }

  // maybe use placeholder somehow. it was previously jammed into the helperText field,
  // but allowing ui:help to grab that spot seems much more appropriate.

  return (
    <Select
      id={id}
      name={id}
      labelText=""
      select
      helperText={helperText}
      value={typeof value === 'undefined' ? emptyValue : value}
      disabled={disabled || readonly}
      autoFocus={autofocus}
      error={rawErrors.length > 0}
      onChange={_onChange}
      onBlur={_onBlur}
      onFocus={_onFocus}
      invalid={invalid}
      invalidText={errorMessageForField}
      InputLabelProps={{
        shrink: true,
      }}
      SelectProps={{
        multiple: typeof multiple === 'undefined' ? false : multiple,
      }}
    >
      {(enumOptions as any).map(({ value, label }: any, i: number) => {
        const disabled: any =
          enumDisabled && (enumDisabled as any).indexOf(value) != -1;
        return <SelectItem text={label} value={value} disabled={disabled} />;
      })}
    </Select>
  );
}

export default SelectWidget;
