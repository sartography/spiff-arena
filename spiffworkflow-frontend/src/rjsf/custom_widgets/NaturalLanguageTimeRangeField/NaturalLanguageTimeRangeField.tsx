import { FieldProps, getUiOptions } from '@rjsf/utils';
import { Check, EditCalendar } from '@mui/icons-material';
import {
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
} from '@mui/material';
import { useMemo, useState } from 'react';
import ExtensionExpressionField from '../ExtensionExpressionField/ExtensionExpressionField';

type WorkPeriod = {
  expression?: string;
  start?: string;
  end?: string;
  time_zone?: string;
};

export default function NaturalLanguageTimeRangeField({
  schema,
  uiSchema,
  fieldPathId,
  formData = {},
  onChange,
  onBlur,
  onFocus,
  disabled,
  readonly,
  label,
  name,
  registry,
}: FieldProps<WorkPeriod>) {
  const options = getUiOptions(uiSchema || {});
  const maximumHours = Number(options.maximum_hours || 16);
  const browserTimeZone =
    formData.time_zone ||
    Intl.DateTimeFormat().resolvedOptions().timeZone ||
    'UTC';
  const [exactEditing, setExactEditing] = useState(false);
  const [exactStart, setExactStart] = useState('');
  const [exactEnd, setExactEnd] = useState('');
  const [exactStartChoice, setExactStartChoice] = useState('');
  const [exactEndChoice, setExactEndChoice] = useState('');

  const exactStartChoices = useMemo(
    () =>
      exactEditing ? instantsForLocalTime(exactStart, browserTimeZone) : [],
    [browserTimeZone, exactEditing, exactStart],
  );
  const exactEndChoices = useMemo(
    () => (exactEditing ? instantsForLocalTime(exactEnd, browserTimeZone) : []),
    [browserTimeZone, exactEditing, exactEnd],
  );

  const beginExactEditing = () => {
    setExactStart(toLocalInputValue(formData.start, browserTimeZone));
    setExactEnd(toLocalInputValue(formData.end, browserTimeZone));
    setExactStartChoice('');
    setExactEndChoice('');
    setExactEditing(true);
  };

  const applyExactTimes = (
    markValid: (value: WorkPeriod, assumptions?: string[]) => void,
    showError: (message: string) => void,
    expression: string,
  ) => {
    if (exactStartChoices.length === 0 || exactEndChoices.length === 0) {
      showError('One of those local times does not exist.');
      return;
    }
    const start =
      exactStartChoices.length === 1 ? exactStartChoices[0] : exactStartChoice;
    const end =
      exactEndChoices.length === 1 ? exactEndChoices[0] : exactEndChoice;
    if (!start || !end) {
      showError('Choose a UTC offset for the duplicated local time.');
      return;
    }
    const durationHours =
      (new Date(end).getTime() - new Date(start).getTime()) / 3_600_000;
    if (durationHours <= 0 || durationHours > maximumHours) {
      showError(
        `Exact times must have an end after the start and be no longer than ${maximumHours} hours.`,
      );
      return;
    }
    setExactEditing(false);
    markValid(
      { expression, start, end, time_zone: browserTimeZone },
      ['exact times'],
    );
  };

  return (
    <ExtensionExpressionField
      schema={schema}
      uiSchema={uiSchema}
      fieldPathId={fieldPathId}
      formData={formData}
      onChange={onChange}
      onBlur={onBlur}
      onFocus={onFocus}
      disabled={disabled}
      readonly={readonly}
      label={label}
      name={name}
      registry={registry}
      examples={String(
        options.examples || 'Examples: 12-1, 9-11:30am yesterday, 3-5 8/12',
      )}
      emptyMessage="Enter a time range."
      initialize={(value) => {
        if (value.start && value.end && !value.time_zone) {
          return { ...value, time_zone: browserTimeZone };
        }
        return undefined;
      }}
      renderPreview={(value, assumptions) => {
        if (typeof value.start !== 'string' || typeof value.end !== 'string') {
          return null;
        }
        const preview = formatRange(value.start, value.end, browserTimeZone);
        return preview + (assumptions.length > 0 ? ` (${assumptions.join(', ')})` : '');
      }}
      renderExtra={({ value, expression, markValid, showError }) => {
        if (exactEditing) {
          return (
            <Stack spacing={1.5}>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
                <TextField
                  label="Exact start"
                  type="datetime-local"
                  value={exactStart}
                  onChange={(event) => {
                    setExactStart(event.target.value);
                    setExactStartChoice('');
                  }}
                  fullWidth
                />
                <TextField
                  label="Exact end"
                  type="datetime-local"
                  value={exactEnd}
                  onChange={(event) => {
                    setExactEnd(event.target.value);
                    setExactEndChoice('');
                  }}
                  fullWidth
                />
              </Stack>
              {exactStartChoices.length > 1 && (
                <UtcOffsetSelect
                  id={`${fieldPathId.$id}-start-offset`}
                  label="Start UTC offset"
                  choices={exactStartChoices}
                  timeZone={browserTimeZone}
                  value={exactStartChoice}
                  onChange={setExactStartChoice}
                />
              )}
              {exactEndChoices.length > 1 && (
                <UtcOffsetSelect
                  id={`${fieldPathId.$id}-end-offset`}
                  label="End UTC offset"
                  choices={exactEndChoices}
                  timeZone={browserTimeZone}
                  value={exactEndChoice}
                  onChange={setExactEndChoice}
                />
              )}
              <Box>
                <Button
                  startIcon={<Check />}
                  onClick={() =>
                    applyExactTimes(markValid, showError, expression)
                  }
                  variant="outlined"
                  size="small"
                >
                  Apply exact times
                </Button>
              </Box>
            </Stack>
          );
        }
        if (disabled || readonly) {
          return null;
        }
        return (
          <Button
            startIcon={<EditCalendar />}
            onClick={beginExactEditing}
            size="small"
          >
            Edit exact times
          </Button>
        );
      }}
    />
  );
}

const toLocalInputValue = (value: string | undefined, timeZone: string) => {
  if (!value) {
    return '';
  }
  const parts = localDateTimeParts(new Date(value), timeZone);
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
};

const UtcOffsetSelect = ({
  id,
  label,
  choices,
  timeZone,
  value,
  onChange,
}: {
  id: string;
  label: string;
  choices: string[];
  timeZone: string;
  value: string;
  onChange: (value: string) => void;
}) => (
  <FormControl fullWidth>
    <InputLabel id={`${id}-label`}>{label}</InputLabel>
    <Select
      id={id}
      labelId={`${id}-label`}
      label={label}
      value={value}
      onChange={(event) => onChange(event.target.value)}
    >
      {choices.map((choice) => (
        <MenuItem key={choice} value={choice}>
          {utcOffsetLabel(choice, timeZone)}
        </MenuItem>
      ))}
    </Select>
  </FormControl>
);

const utcOffsetLabel = (instant: string, timeZone: string) => {
  const offset = new Intl.DateTimeFormat('en-US', {
    timeZone,
    timeZoneName: 'longOffset',
  })
    .formatToParts(new Date(instant))
    .find((part) => part.type === 'timeZoneName')?.value;
  return (offset || 'GMT').replace('GMT', 'UTC');
};

const localDateTimeParts = (value: Date, timeZone: string) => {
  const parts = new Intl.DateTimeFormat('en-CA', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
    timeZone,
  }).formatToParts(value);
  return Object.fromEntries(
    parts
      .filter((part) => part.type !== 'literal')
      .map((part) => [part.type, part.value]),
  );
};

const instantsForLocalTime = (value: string, timeZone: string) => {
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/);
  if (!match) {
    return [];
  }
  const expected = {
    year: match[1],
    month: match[2],
    day: match[3],
    hour: match[4],
    minute: match[5],
  };
  const localAsUtc = Date.UTC(
    Number(expected.year),
    Number(expected.month) - 1,
    Number(expected.day),
    Number(expected.hour),
    Number(expected.minute),
  );
  const matches = new Set<string>();
  for (
    let offsetMinutes = -14 * 60;
    offsetMinutes <= 14 * 60;
    offsetMinutes += 15
  ) {
    const candidate = new Date(localAsUtc - offsetMinutes * 60_000);
    const actual = localDateTimeParts(candidate, timeZone);
    if (Object.entries(expected).every(([key, part]) => actual[key] === part)) {
      matches.add(candidate.toISOString());
    }
  }
  return [...matches].sort();
};

const formatRange = (
  startValue: string,
  endValue: string,
  timeZone = 'UTC',
) => {
  try {
    const formatter = new Intl.DateTimeFormat(undefined, {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      timeZone,
      timeZoneName: 'short',
    });
    return formatter.formatRange(new Date(startValue), new Date(endValue));
  } catch (_error) {
    return `${startValue} - ${endValue}`;
  }
};
