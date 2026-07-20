import { useCallback } from 'react';
import { TextField } from '@mui/material';
// The library intentionally exports its default component as DatePicker.
// eslint-disable-next-line import-x/no-named-as-default
import DatePicker from 'react-datepicker';
import {
  DATE_FORMAT,
  DATE_FORMAT_FOR_DISPLAY,
  DATE_RANGE_DELIMITER,
} from '../../../config';
import { getCommonAttributes } from '../../helpers';
import DateAndTimeService from '../../../services/DateAndTimeService';

interface WidgetArgs {
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
}: WidgetArgs) {
  const commonAttributes = getCommonAttributes(
    label,
    schema,
    uiSchema,
    rawErrors,
  );

  const onChangeLocal = useCallback(
    (dateRange: (Date | null)[]) => {
      let dateRangeString;
      const startDate = dateRange[0]
        ? DateAndTimeService.convertDateObjectToFormattedString(dateRange[0])
        : null;
      if (startDate) {
        const startDateYMD =
          DateAndTimeService.dateStringToYMDFormat(startDate);
        const endDate = dateRange[1]
          ? DateAndTimeService.convertDateObjectToFormattedString(dateRange[1])
          : null;
        dateRangeString = startDateYMD;
        if (endDate) {
          const endDateYMD = DateAndTimeService.dateStringToYMDFormat(endDate);
          dateRangeString = `${dateRangeString}${DATE_RANGE_DELIMITER}${endDateYMD}`;
        }
      }
      onChange(dateRangeString);
    },
    [onChange],
  );

  let dateValue: (Date | null)[] | null = value;
  if (value) {
    const [startDateString, endDateString] = value.split(DATE_RANGE_DELIMITER);
    let startDate = null;
    let endDate = null;
    try {
      startDate = DateAndTimeService.convertStringToDate(startDateString);
    } catch (_rangeError) {}
    try {
      endDate = DateAndTimeService.convertStringToDate(endDateString);
    } catch (_rangeError) {}

    dateValue = [startDate, endDate];
  }

  return (
    <div className="date-input">
      <DatePicker
        id={`${id}-start`}
        selected={dateValue?.[0] || null}
        startDate={dateValue?.[0] || null}
        endDate={dateValue?.[1] || null}
        onChange={(date: Date | null) =>
          onChangeLocal([date, dateValue?.[1] || null])
        }
        selectsStart
        dateFormat={DATE_FORMAT}
        placeholderText={DATE_FORMAT_FOR_DISPLAY}
        autoComplete="off"
        disabled={disabled || readonly}
        customInput={
          <TextField
            label="Start date"
            error={commonAttributes.invalid}
            helperText={
              commonAttributes.invalid
                ? commonAttributes.errorMessageForField
                : commonAttributes.helperText
            }
            autoFocus={autofocus}
          />
        }
      />
      <DatePicker
        id={`${id}-end`}
        selected={dateValue?.[1] || null}
        startDate={dateValue?.[0] || null}
        endDate={dateValue?.[1] || null}
        minDate={dateValue?.[0] || undefined}
        onChange={(date: Date | null) =>
          onChangeLocal([dateValue?.[0] || null, date])
        }
        selectsEnd
        dateFormat={DATE_FORMAT}
        placeholderText={DATE_FORMAT_FOR_DISPLAY}
        autoComplete="off"
        disabled={disabled || readonly}
        customInput={
          <TextField
            label="End date"
            error={commonAttributes.invalid}
            autoFocus={autofocus}
          />
        }
      />
    </div>
  );
}
