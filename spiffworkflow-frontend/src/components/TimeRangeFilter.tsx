import {
  Check as CheckIcon,
  ExpandLess,
  ExpandMore,
  Search as SearchIcon,
} from '@mui/icons-material';
import {
  Box,
  Button,
  Checkbox,
  Divider,
  FormControlLabel,
  InputAdornment,
  ListItemIcon,
  ListItemText,
  MenuItem,
  MenuList,
  Popover,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { KeyboardEvent, useEffect, useMemo, useRef, useState } from 'react';
// react-datepicker intentionally gives its default export the same name as a named type.
// eslint-disable-next-line import-x/no-named-as-default
import DatePicker from 'react-datepicker';

type RelativeRange = {
  id: string;
  label: string;
  shortLabel: string;
  seconds: number;
};

type Props = {
  startTimestamp?: number | null;
  endTimestamp?: number | null;
  onApply: (startTimestamp: number, endTimestamp: number) => void;
};

export const RELATIVE_TIME_RANGES: RelativeRange[] = [
  { id: '1h', label: 'Last hour', shortLabel: '1H', seconds: 60 * 60 },
  {
    id: '24h',
    label: 'Last 24 hours',
    shortLabel: '24H',
    seconds: 24 * 60 * 60,
  },
  { id: '7d', label: 'Last 7 days', shortLabel: '7D', seconds: 7 * 86400 },
  {
    id: '14d',
    label: 'Last 14 days',
    shortLabel: '14D',
    seconds: 14 * 86400,
  },
  {
    id: '30d',
    label: 'Last 30 days',
    shortLabel: '30D',
    seconds: 30 * 86400,
  },
  {
    id: '90d',
    label: 'Last 90 days',
    shortLabel: '90D',
    seconds: 90 * 86400,
  },
];

export const parseRelativeTimeRange = (
  value: string,
  nowSeconds = Math.floor(Date.now() / 1000),
) => {
  const match = value.trim().match(/^(\d+)\s*([mhdw])$/i);
  if (!match || Number(match[1]) < 1) {
    return null;
  }
  const amount = Number(match[1]);
  const unit = match[2].toLowerCase();
  const secondsPerUnit: Record<string, number> = {
    m: 60,
    h: 3600,
    d: 86400,
    w: 604800,
  };
  return {
    startTimestamp: nowSeconds - amount * secondsPerUnit[unit],
    endTimestamp: nowSeconds,
    shortLabel: `${amount}${unit.toUpperCase()}`,
  };
};

const timeParts = (timestamp: number, utc: boolean) => {
  const date = new Date(timestamp * 1000);
  const hours = utc ? date.getUTCHours() : date.getHours();
  const minutes = utc ? date.getUTCMinutes() : date.getMinutes();
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
};

const pickerDate = (timestamp: number, utc: boolean) => {
  const date = new Date(timestamp * 1000);
  return utc
    ? new Date(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate())
    : date;
};

export const dateAndTimeToTimestamp = (
  date: Date,
  time: string,
  utc: boolean,
) => {
  const [hours, minutes] = time.split(':').map(Number);
  const milliseconds = utc
    ? Date.UTC(
        date.getFullYear(),
        date.getMonth(),
        date.getDate(),
        hours,
        minutes,
      )
    : new Date(
        date.getFullYear(),
        date.getMonth(),
        date.getDate(),
        hours,
        minutes,
      ).getTime();
  return Math.floor(milliseconds / 1000);
};

export const getTimeInputPreferences = (locale?: string) => {
  const preferences = new Intl.DateTimeFormat(locale, {
    hour: 'numeric',
  }).resolvedOptions();
  return {
    locale: preferences.locale,
    uses24HourClock: preferences.hour12 === false,
  };
};

const absoluteRangeLabel = (start: Date, end: Date) => {
  const format = new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
  });
  return `${format.format(start)}–${format.format(end)}`;
};

export default function TimeRangeFilter({
  startTimestamp,
  endTimestamp,
  onApply,
}: Props) {
  const [anchorElement, setAnchorElement] = useState<HTMLElement | null>(null);
  const [view, setView] = useState<'presets' | 'absolute'>('presets');
  const [activeRangeId, setActiveRangeId] = useState<string | null>(null);
  const [buttonLabel, setButtonLabel] = useState('Time range');
  const [customRange, setCustomRange] = useState('');
  const [customRangeInvalid, setCustomRangeInvalid] = useState(false);
  const [useUtc, setUseUtc] = useState(true);
  const [absoluteStart, setAbsoluteStart] = useState<Date | null>(null);
  const [absoluteEnd, setAbsoluteEnd] = useState<Date | null>(null);
  const [startTime, setStartTime] = useState('00:00');
  const [endTime, setEndTime] = useState('23:59');
  const lastApplied = useRef<{ start: number; end: number } | null>(null);
  const timeInputPreferences = useMemo(() => getTimeInputPreferences(), []);

  useEffect(() => {
    if (!startTimestamp || !endTimestamp) {
      setActiveRangeId(null);
      setButtonLabel('Time range');
      lastApplied.current = null;
      return;
    }
    if (
      lastApplied.current?.start === startTimestamp &&
      lastApplied.current?.end === endTimestamp
    ) {
      return;
    }
    const start = pickerDate(startTimestamp, useUtc);
    const end = pickerDate(endTimestamp, useUtc);
    setAbsoluteStart(start);
    setAbsoluteEnd(end);
    setStartTime(timeParts(startTimestamp, useUtc));
    setEndTime(timeParts(endTimestamp, useUtc));
    setActiveRangeId('absolute');
    setButtonLabel(absoluteRangeLabel(start, end));
  }, [endTimestamp, startTimestamp, useUtc]);

  const applyRange = (
    start: number,
    end: number,
    rangeId: string,
    label: string,
  ) => {
    lastApplied.current = { start, end };
    setActiveRangeId(rangeId);
    setButtonLabel(label);
    onApply(start, end);
    setAnchorElement(null);
    setView('presets');
  };

  const selectRelativeRange = (range: RelativeRange) => {
    const end = Math.floor(Date.now() / 1000);
    applyRange(end - range.seconds, end, range.id, range.shortLabel);
  };

  const applyCustomRange = () => {
    const parsed = parseRelativeTimeRange(customRange);
    if (!parsed) {
      setCustomRangeInvalid(true);
      return;
    }
    setCustomRangeInvalid(false);
    applyRange(
      parsed.startTimestamp,
      parsed.endTimestamp,
      `custom-${parsed.shortLabel}`,
      parsed.shortLabel,
    );
  };

  const openAbsolutePicker = () => {
    if (startTimestamp && endTimestamp) {
      setAbsoluteStart(pickerDate(startTimestamp, useUtc));
      setAbsoluteEnd(pickerDate(endTimestamp, useUtc));
      setStartTime(timeParts(startTimestamp, useUtc));
      setEndTime(timeParts(endTimestamp, useUtc));
    } else {
      const today = new Date();
      setAbsoluteStart(today);
      setAbsoluteEnd(today);
    }
    setView('absolute');
  };

  const applyAbsoluteRange = () => {
    if (!absoluteStart || !absoluteEnd) {
      return;
    }
    const start = dateAndTimeToTimestamp(absoluteStart, startTime, useUtc);
    const end = dateAndTimeToTimestamp(absoluteEnd, endTime, useUtc);
    if (start > end) {
      return;
    }
    applyRange(
      start,
      end,
      'absolute',
      absoluteRangeLabel(absoluteStart, absoluteEnd),
    );
  };

  return (
    <>
      <Button
        variant="outlined"
        size="small"
        data-testid="time-range-filter-button"
        aria-haspopup="true"
        aria-expanded={Boolean(anchorElement)}
        onClick={(event) => setAnchorElement(event.currentTarget)}
        endIcon={anchorElement ? <ExpandLess /> : <ExpandMore />}
        sx={{ minWidth: 96, whiteSpace: 'nowrap' }}
      >
        {buttonLabel}
      </Button>
      <Popover
        open={Boolean(anchorElement)}
        anchorEl={anchorElement}
        onClose={() => {
          setAnchorElement(null);
          setView('presets');
        }}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        slotProps={{
          paper: {
            sx: {
              mt: 0.5,
              width: view === 'absolute' ? 390 : 330,
              maxWidth: '95vw',
            },
          },
        }}
      >
        <Typography sx={{ fontWeight: 600, px: 2, py: 1.25 }}>
          Filter Time Range
        </Typography>
        <Divider />
        {view === 'presets' ? (
          <>
            <Box sx={{ px: 1, pt: 1 }}>
              <TextField
                autoFocus
                fullWidth
                size="small"
                value={customRange}
                error={customRangeInvalid}
                placeholder="Custom range: 10m, 2h, 4d..."
                inputProps={{ 'aria-label': 'Custom time range' }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon fontSize="small" />
                    </InputAdornment>
                  ),
                }}
                onChange={(event) => {
                  setCustomRange(event.target.value);
                  setCustomRangeInvalid(false);
                }}
                onKeyDown={(event: KeyboardEvent<HTMLInputElement>) => {
                  if (event.key === 'Enter') {
                    applyCustomRange();
                  }
                }}
              />
            </Box>
            <MenuList dense>
              {RELATIVE_TIME_RANGES.map((range) => (
                <MenuItem
                  key={range.id}
                  onClick={() => selectRelativeRange(range)}
                >
                  <ListItemIcon sx={{ minWidth: 30 }}>
                    {activeRangeId === range.id ? (
                      <CheckIcon color="primary" fontSize="small" />
                    ) : null}
                  </ListItemIcon>
                  <ListItemText>{range.label}</ListItemText>
                </MenuItem>
              ))}
              <MenuItem onClick={openAbsolutePicker}>
                <ListItemIcon sx={{ minWidth: 30 }}>
                  {activeRangeId === 'absolute' ? (
                    <CheckIcon color="primary" fontSize="small" />
                  ) : null}
                </ListItemIcon>
                <ListItemText
                  primary="Absolute date"
                  secondary={
                    activeRangeId === 'absolute' ? buttonLabel : undefined
                  }
                />
                <Typography aria-hidden="true">→</Typography>
              </MenuItem>
            </MenuList>
          </>
        ) : (
          <Box data-testid="absolute-time-range-picker">
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 1 }}>
              <DatePicker
                inline
                selectsRange
                selected={absoluteStart}
                startDate={absoluteStart}
                endDate={absoluteEnd}
                onChange={(dates: [Date | null, Date | null]) => {
                  setAbsoluteStart(dates[0]);
                  setAbsoluteEnd(dates[1]);
                }}
              />
            </Box>
            <Divider />
            <Box
              sx={{
                display: 'grid',
                gap: 1,
                gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)',
                p: 1.5,
              }}
            >
              <TextField
                fullWidth
                label="Start time"
                type="time"
                size="small"
                value={startTime}
                onChange={(event) => setStartTime(event.target.value)}
                inputProps={{
                  step: 60,
                  lang: timeInputPreferences.locale,
                  'data-hour-cycle': timeInputPreferences.uses24HourClock
                    ? '24'
                    : '12',
                }}
              />
              <TextField
                fullWidth
                label="End time"
                type="time"
                size="small"
                value={endTime}
                onChange={(event) => setEndTime(event.target.value)}
                inputProps={{
                  step: 60,
                  lang: timeInputPreferences.locale,
                  'data-hour-cycle': timeInputPreferences.uses24HourClock
                    ? '24'
                    : '12',
                }}
              />
              <FormControlLabel
                sx={{ gridColumn: '1 / -1', mr: 0 }}
                control={
                  <Checkbox
                    size="small"
                    checked={useUtc}
                    onChange={(event) => setUseUtc(event.target.checked)}
                  />
                }
                label="UTC"
              />
            </Box>
            <Divider />
            <Stack direction="row" justifyContent="space-between" sx={{ p: 1 }}>
              <Button onClick={() => setView('presets')}>← Back</Button>
              <Button
                variant="contained"
                onClick={applyAbsoluteRange}
                disabled={!absoluteStart || !absoluteEnd}
              >
                Apply
              </Button>
            </Stack>
          </Box>
        )}
      </Popover>
    </>
  );
}
