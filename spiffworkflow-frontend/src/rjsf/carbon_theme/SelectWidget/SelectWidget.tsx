import { Select, SelectItem } from '@carbon/react';
import {
  FormContextType,
  RJSFSchema,
  StrictRJSFSchema,
  WidgetProps,
} from '@rjsf/utils';
import { ChangeEvent, FocusEvent } from 'react';
import { getCommonAttributes } from '../../helpers';

function SelectWidget<
  T = any,
  S extends StrictRJSFSchema = RJSFSchema,
  F extends FormContextType = any,
>({
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
}: WidgetProps<T, S, F>) {
  const { enumOptions } = options;
  let { enumDisabled } = options;

  const emptyValue = multiple ? [] : '';

  const _onChange = ({ target: { value } }: ChangeEvent<{ value: string }>) => {
    onChange(value);
  };

  const _onBlur = ({ target: { value } }: FocusEvent<HTMLInputElement>) => {
    onBlur(id, value);
  };
  const _onFocus = ({ target: { value } }: FocusEvent<HTMLInputElement>) =>
    onFocus(id, value);

  const commonAttributes = getCommonAttributes(
    label,
    schema,
    uiSchema,
    rawErrors,
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
