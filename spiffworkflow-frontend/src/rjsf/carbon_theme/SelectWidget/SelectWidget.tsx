import { Select, SelectItem } from '@carbon/react';
import { WidgetProps } from '@rjsf/utils';
import { getCommonAttributes } from '../../helpers';

// this guessType, asNumber, and processSelectValue code is pulled from rjsf/utils version 5.0.0-beta.20
// the function was removed.
/** Given a specific `value` attempts to guess the type of a schema element. In the case where we have to implicitly
 *  create a schema, it is useful to know what type to use based on the data we are defining.
 *
 * @param value - The value from which to guess the type
 * @returns - The best guess for the object type
 */
function guessType(value) {
  if (Array.isArray(value)) {
    return 'array';
  }
  if (typeof value === 'string') {
    return 'string';
  }
  if (value == null) {
    return 'null';
  }
  if (typeof value === 'boolean') {
    return 'boolean';
  }
  if (!isNaN(value)) {
    return 'number';
  }
  if (typeof value === 'object') {
    return 'object';
  }
  // Default to string if we can't figure it out
  return 'string';
}

/** Attempts to convert the string into a number. If an empty string is provided, then `undefined` is returned. If a
 * `null` is provided, it is returned. If the string ends in a `.` then the string is returned because the user may be
 * in the middle of typing a float number. If a number ends in a pattern like `.0`, `.20`, `.030`, string is returned
 * because the user may be typing number that will end in a non-zero digit. Otherwise, the string is wrapped by
 * `Number()` and if that result is not `NaN`, that number will be returned, otherwise the string `value` will be.
 *
 * @param value - The string or null value to convert to a number
 * @returns - The `value` converted to a number when appropriate, otherwise the `value`
 */
function asNumber(value) {
  if (value === '') {
    return undefined;
  }
  if (value === null) {
    return null;
  }
  if (/\.$/.test(value)) {
    // '3.' can't really be considered a number even if it parses in js. The
    // user is most likely entering a float.
    return value;
  }
  if (/\.0$/.test(value)) {
    // we need to return this as a string here, to allow for input like 3.07
    return value;
  }
  if (/\.\d*0$/.test(value)) {
    // It's a number, that's cool - but we need it as a string so it doesn't screw
    // with the user when entering dollar amounts or other values (such as those with
    // specific precision or number of significant digits)
    return value;
  }
  var n = Number(value);
  var valid = typeof n === 'number' && !Number.isNaN(n);
  return valid ? n : value;
}

function get(object, path) {
  // Split the path into an array of keys
  const keys = Array.isArray(path) ? path : path.split('.');

  // Traverse the object along the keys
  let result = object;
  for (let key of keys) {
    if (result == null) {
      return undefined; // If the path does not exist, return undefined
    }
    result = result[key];
  }

  return result; // Return the found value or undefined if not found
}

var nums = /*#__PURE__*/ new Set(['number', 'integer']);
/** Returns the real value for a select widget due to a silly limitation in the DOM which causes option change event
 * values to always be retrieved as strings. Uses the `schema` to help determine the value's true type. If the value is
 * an empty string, then the `emptyValue` from the `options` is returned, falling back to undefined.
 *
 * @param schema - The schema to used to determine the value's true type
 * @param [value] - The value to convert
 * @param [options] - The UIOptionsType from which to potentially extract the emptyValue
 * @returns - The `value` converted to the proper type
 */
function processSelectValue(schema, value, options) {
  var schemaEnum = schema['enum'],
    type = schema.type,
    items = schema.items;
  if (value === '') {
    return options && options.emptyValue !== undefined
      ? options.emptyValue
      : undefined;
  }
  if (type === 'array' && items && nums.has(get(items, 'type'))) {
    return value.map(asNumber);
  }
  if (type === 'boolean') {
    return value === 'true';
  }
  if (nums.has(type)) {
    return asNumber(value);
  }
  // If type is undefined, but an enum is present, try and infer the type from
  // the enum values
  if (Array.isArray(schemaEnum)) {
    if (
      schemaEnum.every(function (x) {
        return nums.has(guessType(x));
      })
    ) {
      return asNumber(value);
    }
    if (
      schemaEnum.every(function (x) {
        return guessType(x) === 'boolean';
      })
    ) {
      return value === 'true';
    }
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
