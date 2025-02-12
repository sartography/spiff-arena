import { DatePicker, DatePickerInput, TextInput } from '@carbon/react';
import {
  getInputProps,
  FormContextType,
  RJSFSchema,
  StrictRJSFSchema,
  WidgetProps,
  examplesId,
  ariaDescribedByIds,
} from '@rjsf/utils';

import { useCallback } from 'react';
import { useDebouncedCallback } from 'use-debounce';
import { DATE_FORMAT_CARBON, DATE_FORMAT_FOR_DISPLAY } from '../../../config';
import DateAndTimeService from '../../../services/DateAndTimeService';
import { getCommonAttributes } from '../../helpers';

/** The `BaseInputTemplate` is the template to use to render the basic `<input>` component for the `core` theme.
 * It is used as the template for rendering many of the <input> based widgets that differ by `type` and callbacks only.
 * It can be customized/overridden for other themes or individual implementations as needed.
 *
 * @param props - The `WidgetProps` for this template
 */
export default function BaseInputTemplate<
  T = any,
  S extends StrictRJSFSchema = RJSFSchema,
  F extends FormContextType = any,
>(props: WidgetProps<T, S, F>) {
  const {
    id,
    value,
    readonly,
    disabled,
    autofocus,
    label,
    onBlur,
    onFocus,
    onChange,
    onChangeOverride,
    required,
    options,
    schema,
    uiSchema,
    formContext,
    registry,
    rawErrors,
    type,
    ...rest
  } = props;

  // Note: since React 15.2.0 we can't forward unknown element attributes, so we
  // exclude the "options" and "schema" ones here.
  if (!id) {
    throw new Error(`no id for props ${JSON.stringify(props)}`);
  }
  const inputProps = {
    ...rest,
    ...getInputProps<T, S, F>(schema, type, options),
  };

  const _onChange = useCallback(
    ({ target }: React.ChangeEvent<HTMLInputElement>) => {
      onChange(target.value === '' ? options.emptyValue : target.value);
    },
    [onChange, options],
  );
  const _onBlur = useCallback(
    ({ target }: React.FocusEvent<HTMLInputElement>) =>
      onBlur(id, target.value),
    [onBlur, id],
  );
  const _onFocus = useCallback(
    ({ target }: React.FocusEvent<HTMLInputElement>) =>
      onFocus(id, target.value),
    [onFocus, id],
  );

  const addDebouncedOnChangeDate = useDebouncedCallback(
    (fullObject: React.ChangeEvent<HTMLInputElement>) => {
      fullObject.target.value =
        DateAndTimeService.attemptToConvertUnknownDateStringFormatToKnownFormat(
          fullObject.target.value,
        );
      _onChange(fullObject);
    },
    // delay in ms
    100,
  );

  const addDebouncedOnChangeText = useDebouncedCallback(
    (fullObject: React.ChangeEvent<HTMLInputElement>) => {
      (onChangeOverride || _onChange)(fullObject);
    },
    // delay in ms
    100,
  );

  let enableCounter = false;
  let maxCount = undefined;
  if (options && options.counter) {
    enableCounter = true;
    if (schema && schema.maxLength) {
      maxCount = schema.maxLength;
    } else {
      throw new Error(
        `Counter was requested but no maxLength given on the ${label}`,
      );
    }
  }

  const commonAttributes = getCommonAttributes(
    label,
    schema,
    uiSchema,
    rawErrors,
  );

  let component = null;
  if (type === 'date') {
    // display the date in a date input box as the config wants.
    // it should in be y-m-d when it gets here.
    let dateValue: string | null = value;
    if (value || value === 0) {
      // it would be good if we could compare against the length of the desired format but that doesn't work in all cases and causes some issues.
      // 10 seems to be a good value check against.
      if (value.length < 10) {
        dateValue = value;
      } else {
        try {
          dateValue = DateAndTimeService.ymdDateStringToConfiguredFormat(value);
          // let the date component and form validators handle bad dates and do not blow up
        } catch (RangeError) {}
      }
    }

    component = (
      <DatePicker
        dateFormat={DATE_FORMAT_CARBON}
        className="date-input"
        datePickerType="single"
      >
        <DatePickerInput
          id={id}
          placeholder={DATE_FORMAT_FOR_DISPLAY}
          helperText={commonAttributes.helperText}
          type="text"
          labelText=""
          size="md"
          value={dateValue}
          autocomplete="off"
          allowInput={false}
          onChange={addDebouncedOnChangeDate}
          invalid={commonAttributes.invalid}
          invalidText={commonAttributes.errorMessageForField}
          autoFocus={autofocus}
          disabled={disabled || readonly}
          onBlur={_onBlur}
          onFocus={_onFocus}
          pattern={null}
        />
      </DatePicker>
    );
  } else if (type === 'file') {
    component = (
      <input
        id={id}
        className="file-upload"
        readOnly={readonly}
        disabled={disabled}
        autoFocus={autofocus}
        value={value}
        {...inputProps}
        list={schema.examples ? examplesId<T>(id) : undefined}
        onChange={onChangeOverride || _onChange}
        onBlur={_onBlur}
        onFocus={_onFocus}
        aria-describedby={ariaDescribedByIds<T>(id, !!schema.examples)}
      />
    );
  } else {
    component = (
      <>
        <TextInput
          id={id}
          className="text-input"
          labelText=""
          helperText={commonAttributes.helperText}
          invalid={commonAttributes.invalid}
          invalidText={commonAttributes.errorMessageForField}
          autoFocus={autofocus}
          disabled={disabled || readonly}
          defaultValue={value || value === 0 ? value : ''}
          onChange={addDebouncedOnChangeText}
          onBlur={_onBlur}
          onFocus={_onFocus}
          enableCounter={enableCounter}
          maxCount={maxCount}
          // eslint-disable-next-line react/jsx-props-no-spreading
          {...inputProps}
        />
        {Array.isArray(schema.examples) && (
          <datalist key={`datalist_${id}`} id={`examples_${id}`}>
            {[
              ...new Set(
                schema.examples.concat(schema.default ? [schema.default] : []),
              ),
            ].map((example: any) => (
              <option key={example} value={example} />
            ))}
          </datalist>
        )}
      </>
    );
  }
  return component;
}
