import React, { useCallback } from 'react';
import { DatePickerInput, DatePicker } from '@carbon/react';
import {
  DATE_FORMAT_CARBON,
  DATE_FORMAT_FOR_DISPLAY,
  DATE_RANGE_DELIMITER,
} from '../../../config';
import {
  convertDateObjectToFormattedString,
  convertStringToDate,
} from '../../../helpers';

interface widgetArgs {
  id: string;
  value: any;
  schema?: any;
  uiSchema?: any;
  disabled?: boolean;
  readonly?: boolean;
  rawErrors?: any;
  onChange?: any;
  autofocus?: any;
  label?: string;
}

// NOTE: To properly validate that both start and end dates are specified
// use this pattern in schemaJson for that field:
// "pattern": "\\d{4}-\\d{2}-\\d{2}:::\\d{4}-\\d{2}-\\d{2}"

// eslint-disable-next-line sonarjs/cognitive-complexity
export default function DateRangePickerWidget({
  id,
  value,
  schema,
  uiSchema,
  disabled,
  readonly,
  onChange,
  autofocus,
  label,
  rawErrors = [],
}: widgetArgs) {
  let invalid = false;
  let errorMessageForField = null;

  let labelToUse = label;
  if (uiSchema && uiSchema['ui:title']) {
    labelToUse = uiSchema['ui:title'];
  } else if (schema && schema.title) {
    labelToUse = schema.title;
  }

  const onChangeLocal = useCallback(
    (dateRange: Date[]) => {
      let dateRangeString;
      const startDate = convertDateObjectToFormattedString(dateRange[0]);
      if (startDate) {
        const endDate = convertDateObjectToFormattedString(dateRange[1]);
        dateRangeString = startDate;
        if (endDate) {
          dateRangeString = `${dateRangeString}${DATE_RANGE_DELIMITER}${endDate}`;
        }
      }
      onChange(dateRangeString);
    },
    [onChange]
  );

  let helperText = null;
  if (uiSchema && uiSchema['ui:help']) {
    helperText = uiSchema['ui:help'];
  }

  if (!invalid && rawErrors && rawErrors.length > 0) {
    invalid = true;
    if ('validationErrorMessage' in schema) {
      errorMessageForField = (schema as any).validationErrorMessage;
    } else {
      errorMessageForField = `${(labelToUse || '').replace(/\*$/, '')} ${
        rawErrors[0]
      }`;
    }
  }

  let dateValue: (Date | null)[] | null = value;
  const dateRegex = new RegExp(DATE_RANGE_DELIMITER);
  if (value && dateRegex.test(value)) {
    const [startDateString, endDateString] = value.split(DATE_RANGE_DELIMITER);
    let startDate = null;
    let endDate = null;
    try {
      startDate = convertStringToDate(startDateString);
      // eslint-disable-next-line no-empty
    } catch (RangeError) {}
    try {
      endDate = convertStringToDate(endDateString);
      // eslint-disable-next-line no-empty
    } catch (RangeError) {}

    dateValue = [startDate, endDate];
  }

  return (
    <DatePicker
      className="date-input"
      datePickerType="range"
      dateFormat={DATE_FORMAT_CARBON}
      onChange={onChangeLocal}
      value={dateValue}
    >
      <DatePickerInput
        id={`${id}-start`}
        placeholder={DATE_FORMAT_FOR_DISPLAY}
        helperText={helperText}
        type="text"
        size="md"
        disabled={disabled || readonly}
        invalid={invalid}
        invalidText={errorMessageForField}
        autoFocus={autofocus}
        pattern={null}
      />
      <DatePickerInput
        id={`${id}-end`}
        placeholder={DATE_FORMAT_FOR_DISPLAY}
        helperText={helperText}
        type="text"
        size="md"
        disabled={disabled || readonly}
        invalid={invalid}
        autoFocus={autofocus}
        pattern={null}
      />
    </DatePicker>
  );
}
