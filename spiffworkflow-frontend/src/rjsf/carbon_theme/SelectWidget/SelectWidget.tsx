import { Select, SelectItem } from '@carbon/react';
import { WidgetProps } from '@rjsf/utils';
import { getCommonAttributes } from '../../helpers';

function processSelectValue(schema: any, value: any, options: any) {
  if (schema.type === 'array' && schema.items && options?.enumOptions) {
    return value.map((value: any) => {
      const option = options.enumOptions.find(
        (option: any) => option.value === value
      );
      return option ? option.value : value;
    });
  }
  if (schema.type === 'boolean') {
    return value === 'true';
  }
  return value;
}

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
  const { enumOptions } = options;
  let { enumDisabled } = options;

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

  const commonAttributes = getCommonAttributes(
    label,
    schema,
    uiSchema,
    rawErrors
  );

  // ok. so in safari, the select widget showed the first option, whereas in chrome it forced you to select an option.
  // this change causes causes safari to act a little bit more like chrome, but it's different because we are actually adding
  // an element to the dropdown.
  //
  // https://stackoverflow.com/a/7944490/6090676 safari detection
  let isSafari = false;
  const ua = navigator.userAgent.toLowerCase();
  if (ua.indexOf('safari') != -1) {
    if (ua.indexOf('chrome') === -1) {
      isSafari = true;
    }
  }

  if (isSafari) {
    if (enumOptions && enumOptions[0].value !== '') {
      enumOptions.unshift({
        value: '',
        label: '',
      });
    }
    // enumDisabled is a list of values for which the option should be disabled.
    // we don't really want users to select the fake empty option we are creating here.
    // they cannot select it in chrome, after all.
    // google is always right. https://news.ycombinator.com/item?id=35862041
    if (enumDisabled === undefined) {
      enumDisabled = [];
    }
    enumDisabled.push('');
  }

  // maybe use placeholder somehow. it was previously jammed into the helperText field,
  // but allowing ui:help to grab that spot seems much more appropriate.

  return (
    <Select
      id={id}
      name={id}
      labelText=""
      select
      helperText={commonAttributes.helperText}
      value={typeof value === 'undefined' ? emptyValue : value}
      disabled={disabled || readonly}
      autoFocus={autofocus}
      error={rawErrors.length > 0}
      onChange={_onChange}
      onBlur={_onBlur}
      onFocus={_onFocus}
      invalid={commonAttributes.invalid}
      invalidText={commonAttributes.errorMessageForField}
      InputLabelProps={{
        shrink: true,
      }}
      SelectProps={{
        multiple: typeof multiple === 'undefined' ? false : multiple,
      }}
    >
      {(enumOptions as any).map(({ value, label }: any, _i: number) => {
        const disabled: any =
          enumDisabled && (enumDisabled as any).indexOf(value) != -1;
        return <SelectItem text={label} value={value} disabled={disabled} />;
      })}
    </Select>
  );
}

export default SelectWidget;
