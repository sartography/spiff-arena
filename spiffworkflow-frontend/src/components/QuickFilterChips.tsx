import { Box, Chip } from '@mui/material';
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { ReportFilter, ReportMetadata } from '../interfaces';

type QuickFilterPreset = {
  id: string;
  label: string;
  buildFilters: () => ReportFilter[];
  // Whose filters this preset "owns" — used to detect active state and to clear.
  ownedFields: string[];
};

const equalsFilter = (fieldName: string, fieldValue: any): ReportFilter => ({
  field_name: fieldName,
  field_value: fieldValue,
  operator: 'equals',
});

const buildPresets = (t: (k: string) => string): QuickFilterPreset[] => [
  {
    id: 'errors',
    label: t('quick_filter_errors'),
    ownedFields: ['process_status'],
    buildFilters: () => [equalsFilter('process_status', 'error')],
  },
  {
    id: 'active',
    label: t('quick_filter_active'),
    ownedFields: ['process_status'],
    buildFilters: () => [
      equalsFilter('process_status', 'running,waiting,user_input_required'),
    ],
  },
  {
    id: 'completed',
    label: t('quick_filter_completed'),
    ownedFields: ['process_status'],
    buildFilters: () => [equalsFilter('process_status', 'complete')],
  },
];

type Props = {
  activePresetIds: string[];
  reportMetadata: ReportMetadata | null;
  onApplyPreset: (
    addFilters: ReportFilter[],
    clearFieldNames: string[],
    presetId: string,
    isActive: boolean,
  ) => void;
};

export default function QuickFilterChips({
  activePresetIds,
  reportMetadata,
  onApplyPreset,
}: Props) {
  const { t } = useTranslation();
  const presets = useMemo(() => buildPresets(t), [t]);
  if (!reportMetadata) {
    return null;
  }

  const handleClick = (preset: QuickFilterPreset) => {
    const active = activePresetIds.includes(preset.id);
    if (active) {
      onApplyPreset([], preset.ownedFields, preset.id, active);
    } else {
      onApplyPreset(
        preset.buildFilters(),
        preset.ownedFields,
        preset.id,
        active,
      );
    }
  };

  return (
    <Box
      sx={{
        alignItems: 'center',
        display: 'flex',
        flexWrap: 'wrap',
        gap: 0.5,
      }}
    >
      {presets.map((preset) => {
        const active = activePresetIds.includes(preset.id);
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
    </Box>
  );
}
