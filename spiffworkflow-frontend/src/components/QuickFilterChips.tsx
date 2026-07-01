import { Chip, Stack } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { ReportFilter, ReportMetadata } from '../interfaces';

type QuickFilterPreset = {
  id: string;
  label: string;
  filters: ReportFilter[];
  // Whose filters this preset "owns" — used to detect active state and to clear.
  ownedFields: string[];
};

const startOfTodaySeconds = (): number => {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  return Math.floor(d.getTime() / 1000);
};

const daysAgoSeconds = (days: number): number => {
  return Math.floor(Date.now() / 1000) - days * 86400;
};

const buildPresets = (t: (k: string) => string): QuickFilterPreset[] => [
  {
    id: 'errors',
    label: t('quick_filter_errors'),
    ownedFields: ['process_status'],
    filters: [
      {
        field_name: 'process_status',
        field_value: 'error',
        operator: 'equals',
      },
    ],
  },
  {
    id: 'active',
    label: t('quick_filter_active'),
    ownedFields: ['process_status'],
    filters: [
      {
        field_name: 'process_status',
        field_value: 'running,waiting,user_input_required',
        operator: 'equals',
      },
    ],
  },
  {
    id: 'completed',
    label: t('quick_filter_completed'),
    ownedFields: ['process_status'],
    filters: [
      {
        field_name: 'process_status',
        field_value: 'complete',
        operator: 'equals',
      },
    ],
  },
  {
    id: 'today',
    label: t('quick_filter_today'),
    ownedFields: ['start_from'],
    filters: [
      {
        field_name: 'start_from',
        field_value: startOfTodaySeconds(),
        operator: 'equals',
      },
    ],
  },
  {
    id: 'last_7_days',
    label: t('quick_filter_last_7_days'),
    ownedFields: ['start_from'],
    filters: [
      {
        field_name: 'start_from',
        field_value: daysAgoSeconds(7),
        operator: 'equals',
      },
    ],
  },
];

const isPresetActive = (
  preset: QuickFilterPreset,
  filterBy: ReportFilter[],
): boolean => {
  return preset.filters.every((presetFilter) =>
    filterBy.some(
      (f) =>
        f.field_name === presetFilter.field_name &&
        String(f.field_value) === String(presetFilter.field_value) &&
        f.operator === presetFilter.operator,
    ),
  );
};

type Props = {
  reportMetadata: ReportMetadata | null;
  onApplyPreset: (
    addFilters: ReportFilter[],
    clearFieldNames: string[],
  ) => void;
};

export default function QuickFilterChips({
  reportMetadata,
  onApplyPreset,
}: Props) {
  const { t } = useTranslation();
  if (!reportMetadata) {
    return null;
  }

  const presets = buildPresets(t);
  const filterBy = reportMetadata.filter_by;

  const handleClick = (preset: QuickFilterPreset) => {
    if (isPresetActive(preset, filterBy)) {
      onApplyPreset([], preset.ownedFields);
    } else {
      onApplyPreset(preset.filters, preset.ownedFields);
    }
  };

  return (
    <Stack
      direction="row"
      spacing={1}
      sx={{ alignItems: 'center', flexWrap: 'wrap', rowGap: 1 }}
    >
      {presets.map((preset) => {
        const active = isPresetActive(preset, filterBy);
        return (
          <Chip
            key={preset.id}
            label={preset.label}
            color={active ? 'primary' : 'default'}
            variant={active ? 'filled' : 'outlined'}
            onClick={() => handleClick(preset)}
            onDelete={active ? () => handleClick(preset) : undefined}
            size="small"
          />
        );
      })}
    </Stack>
  );
}
