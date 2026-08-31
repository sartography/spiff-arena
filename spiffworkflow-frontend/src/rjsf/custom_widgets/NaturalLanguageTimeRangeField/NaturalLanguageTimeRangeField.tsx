import { FieldProps, getUiOptions } from '@rjsf/utils';
import { Check, EditCalendar } from '@mui/icons-material';
import {
  Box,
  Button,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { KeyboardEvent, useEffect, useMemo, useRef, useState } from 'react';
import HttpService from '../../../services/HttpService';

type WorkPeriod = {
  expression?: string;
  start?: string;
  end?: string;
  time_zone?: string;
};

type ResolverResult = {
  status: 'valid' | 'invalid' | 'ambiguous';
  value?: WorkPeriod;
  assumptions?: string[];
  errors?: { code: string; message: string }[];
};

const errorSchema = (message: string) => ({ __errors: [message] });

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
  required,
  label,
}: FieldProps<WorkPeriod>) {
  const options = getUiOptions(uiSchema || {});
  const resolver = String(options.resolver || '');
  const dateOrder = String(options.dateOrder || 'MDY');
  const preferCompletedRange = options.preferCompletedRange !== false;
  const maximumHours = Number(options.maximumHours || 16);
  const idleMilliseconds = Number(options.idleMilliseconds || 500);
  const browserTimeZone =
    formData.time_zone ||
    Intl.DateTimeFormat().resolvedOptions().timeZone ||
    'UTC';
  const [expression, setExpression] = useState(formData.expression || '');
  const [assumptions, setAssumptions] = useState<string[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [exactEditing, setExactEditing] = useState(false);
  const [exactStart, setExactStart] = useState('');
  const [exactEnd, setExactEnd] = useState('');
  const [exactStartChoice, setExactStartChoice] = useState('');
  const [exactEndChoice, setExactEndChoice] = useState('');
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const requestRef = useRef<{ controller: AbortController; id: number } | null>(
    null,
  );
  const requestIdRef = useRef(0);

  useEffect(() => {
    if (formData.start && formData.end && !formData.time_zone) {
      onChange(
        { ...formData, time_zone: browserTimeZone },
        fieldPathId.path,
        undefined,
        fieldPathId.$id,
      );
    }
  }, [browserTimeZone, fieldPathId.$id, fieldPathId.path, formData, onChange]);

  useEffect(
    () => () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      requestRef.current?.controller.abort();
    },
    [],
  );

  const emitError = (nextValue: WorkPeriod, errorMessage: string) => {
    setMessage(errorMessage);
    onChange(
      nextValue,
      fieldPathId.path,
      errorSchema(errorMessage),
      fieldPathId.$id,
    );
  };

  const parse = (value: string) => {
    if (!value.trim()) {
      emitError({ ...formData, expression: value }, 'Enter a time range.');
      return;
    }
    if (!resolver.match(/^[a-zA-Z0-9][a-zA-Z0-9/_-]*$/)) {
      emitError(
        { ...formData, expression: value },
        'The configured time-range resolver is invalid.',
      );
      return;
    }

    requestRef.current?.controller.abort();
    const controller = new AbortController();
    requestIdRef.current += 1;
    const requestId = requestIdRef.current;
    requestRef.current = { controller, id: requestId };
    setLoading(true);
    setMessage(null);

    const resolvedOptions = Intl.DateTimeFormat().resolvedOptions();
    HttpService.makeCallToBackend({
      path: `/v1.0/extensions/${resolver}`,
      httpMethod: 'POST',
      signal: controller.signal,
      postBody: {
        extension_input: {
          expression: value,
          reference_instant: new Date().toISOString(),
          time_zone: resolvedOptions.timeZone,
          locale: resolvedOptions.locale,
          date_order: dateOrder,
          prefer_completed_range: preferCompletedRange,
          maximum_hours: maximumHours,
        },
      },
      successCallback: (response: {
        task_data?: { result?: ResolverResult };
      }) => {
        if (requestIdRef.current !== requestId) {
          return;
        }
        setLoading(false);
        const result = response.task_data?.result;
        if (result?.status === 'valid' && result.value) {
          setAssumptions(result.assumptions || []);
          setMessage(null);
          onChange(result.value, fieldPathId.path, undefined, fieldPathId.$id);
          return;
        }
        const resultMessage =
          result?.errors?.[0]?.message ||
          'The time range could not be interpreted.';
        emitError({ ...formData, expression: value }, resultMessage);
      },
      failureCallback: (error: { name?: string }) => {
        if (
          requestIdRef.current !== requestId ||
          error?.name === 'AbortError'
        ) {
          return;
        }
        setLoading(false);
        emitError(
          { ...formData, expression: value },
          'The time range could not be checked. Your last valid times are unchanged.',
        );
      },
    });
  };

  const scheduleParse = (value: string) => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    timerRef.current = setTimeout(() => parse(value), idleMilliseconds);
  };

  const updateExpression = (value: string) => {
    setExpression(value);
    setAssumptions([]);
    const nextValue = { ...formData, expression: value };
    onChange(
      nextValue,
      fieldPathId.path,
      errorSchema('Interpretation pending.'),
      fieldPathId.$id,
    );
    scheduleParse(value);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      parse(expression);
    }
  };

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
    setMessage(null);
  };

  const applyExactTimes = () => {
    if (exactStartChoices.length === 0 || exactEndChoices.length === 0) {
      emitError(
        { ...formData, expression },
        'One of those local times does not exist.',
      );
      return;
    }
    const start =
      exactStartChoices.length === 1 ? exactStartChoices[0] : exactStartChoice;
    const end =
      exactEndChoices.length === 1 ? exactEndChoices[0] : exactEndChoice;
    if (!start || !end) {
      emitError(
        { ...formData, expression },
        'Choose a UTC offset for the duplicated local time.',
      );
      return;
    }
    const durationHours =
      (new Date(end).getTime() - new Date(start).getTime()) / 3_600_000;
    if (durationHours <= 0 || durationHours > maximumHours) {
      emitError(
        { ...formData, expression },
        `Exact times must have an end after the start and be no longer than ${maximumHours} hours.`,
      );
      return;
    }
    setAssumptions(['exact times']);
    setMessage(null);
    setExactEditing(false);
    onChange(
      { expression, start, end, time_zone: browserTimeZone },
      fieldPathId.path,
      undefined,
      fieldPathId.$id,
    );
  };

  const preview =
    formData.start && formData.end
      ? formatRange(formData.start, formData.end, browserTimeZone)
      : null;
  const title = schema.title || label || 'Time range';

  return (
    <Stack spacing={1.5}>
      <TextField
        id={`${fieldPathId.$id}-expression`}
        label={title}
        required={required}
        disabled={disabled}
        slotProps={{ htmlInput: { readOnly: readonly } }}
        value={expression}
        onChange={(event) => updateExpression(event.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={() => {
          onBlur(fieldPathId.$id, expression);
          if (expression) {
            parse(expression);
          }
        }}
        onFocus={() => onFocus(fieldPathId.$id, expression)}
        error={Boolean(message)}
        helperText={message || 'Examples: 12-1, 9-11:30am yesterday, 3-5 8/12'}
        fullWidth
      />
      {loading && (
        <Box
          sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
          role="status"
        >
          <CircularProgress size={16} />
          <Typography variant="body2">Interpreting time range...</Typography>
        </Box>
      )}
      {preview && (
        <Typography variant="body2" aria-live="polite">
          {preview}
          {assumptions.length > 0 ? ` (${assumptions.join(', ')})` : ''}
        </Typography>
      )}
      {!exactEditing && !disabled && !readonly && (
        <Box>
          <Button
            startIcon={<EditCalendar />}
            onClick={beginExactEditing}
            size="small"
          >
            Edit exact times
          </Button>
        </Box>
      )}
      {exactEditing && (
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
              onClick={applyExactTimes}
              variant="outlined"
              size="small"
            >
              Apply exact times
            </Button>
          </Box>
        </Stack>
      )}
    </Stack>
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
