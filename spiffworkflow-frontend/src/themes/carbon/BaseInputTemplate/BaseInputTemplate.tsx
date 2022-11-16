import React from 'react';
// @ts-ignore
import { TextInput } from '@carbon/react';
import { getInputProps, WidgetProps } from '@rjsf/utils';

function BaseInputTemplate({
  id,
  placeholder,
  required,
  readonly,
  disabled,
  type,
  label,
  value,
  onChange,
  onBlur,
  onFocus,
  autofocus,
  options,
  schema,
  uiSchema,
  rawErrors = [],
  registry,
}: // ...textFieldProps
WidgetProps) {
  const inputProps = getInputProps(schema, type, options);
  // Now we need to pull out the step, min, max into an inner `inputProps` for material-ui
  const { step, min, max, ...rest } = inputProps;
  const otherProps = {
    inputProps: {
      step,
      min,
      max,
      ...(schema.examples ? { list: `examples_${id}` } : undefined),
    },
    ...rest,
  };
  const localOnChange = ({
    // eslint-disable-next-line no-shadow
    target: { value },
  }: React.ChangeEvent<HTMLInputElement>) => {
    onChange(value === '' ? options.emptyValue : value);
  };
  const localOnBlur = ({
    // eslint-disable-next-line no-shadow
    target: { value },
  }: React.FocusEvent<HTMLInputElement>) => onBlur(id, value);
  const localOnFocus = ({
    // eslint-disable-next-line no-shadow
    target: { value },
  }: React.FocusEvent<HTMLInputElement>) => onFocus(id, value);

  const { schemaUtils } = registry;
  const displayLabel = schemaUtils.getDisplayLabel(schema, uiSchema);

  return (
    <>
      <TextInput
        id={id}
        name={id}
        placeholder={placeholder}
        label={displayLabel ? label || schema.title : false}
        autoFocus={autofocus}
        required={required}
        disabled={disabled || readonly}
        value={value || value === 0 ? value : ''}
        error={rawErrors.length > 0}
        onChange={localOnChange}
        onBlur={localOnBlur}
        onFocus={localOnFocus}
        // eslint-disable-next-line react/jsx-props-no-spreading
        {...otherProps}
      />
      {schema.examples && (
        <datalist id={`examples_${id}`}>
          {(schema.examples as string[])
            .concat(schema.default ? ([schema.default] as string[]) : [])
            .map((example: any) => {
              // eslint-disable-next-line jsx-a11y/control-has-associated-label
              return <option key={example} value={example} />;
            })}
        </datalist>
      )}
    </>
  );
}

export default BaseInputTemplate;
