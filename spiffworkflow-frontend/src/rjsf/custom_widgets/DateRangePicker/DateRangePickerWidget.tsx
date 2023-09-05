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
  dateStringToYMDFormat,
} from '../../../helpers';
import { getCommonAttributes } from '../../helpers';

interface widgetArgs {
  id: string;
  value: any;
  label: string;
  schema?: any;
  uiSchema?: any;
  disabled?: boolean;
  readonly?: boolean;
  rawErrors?: any;
  onChange?: any;
  autofocus?: any;
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
  const commonAttributes = getCommonAttributes(
    label,
    schema,
    uiSchema,
    rawErrors
  );

  const onChangeLocal = useCallback(
    (dateRange: Date[]) => {
      let dateRangeString;
      const startDate = convertDateObjectToFormattedString(dateRange[0]);
      if (startDate) {
        const startDateYMD = dateStringToYMDFormat(startDate);
        const endDate = convertDateObjectToFormattedString(dateRange[1]);
        dateRangeString = startDateYMD;
        if (endDate) {
          const endDateYMD = dateStringToYMDFormat(endDate);
          dateRangeString = `${dateRangeString}${DATE_RANGE_DELIMITER}${endDateYMD}`;
        }
      }
      onChange(dateRangeString);
    },
    [onChange]
  );

  let dateValue: (Date | null)[] | null = value;
  if (value) {
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
        helperText={commonAttributes.helperText}
        type="text"
        size="md"
        disabled={disabled || readonly}
        invalid={commonAttributes.invalid}
        invalidText={commonAttributes.errorMessageForField}
        autoFocus={autofocus}
        pattern={null}
      />
      <DatePickerInput
        id={`${id}-end`}
        placeholder={DATE_FORMAT_FOR_DISPLAY}
        type="text"
        size="md"
        disabled={disabled || readonly}
        invalid={commonAttributes.invalid}
        autoFocus={autofocus}
        pattern={null}
      />
    </DatePicker>
  );
}
