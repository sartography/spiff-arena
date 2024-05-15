import { Stack, useTheme } from '@mui/material';
import { BarChart } from '@mui/x-charts/BarChart';

export default function DashboardCharts({
  times,
}: {
  times: Record<string, any>;
}) {
  const { palette } = useTheme();

  return (
    <Stack
      gap={2}
      padding={2}
      direction="row"
      sx={{
        flexWrap: 'wrap',
        width: '100%',
        height: '100%',
      }}
    >
      <BarChart
        borderRadius={4}
        skipAnimation
        margin={{
          left: 50,
          right: 0,
          top: 20,
          bottom: 20,
        }}
        xAxis={[
          {
            scaleType: 'band',
            data: ['PI Status Counts'],
          },
        ]}
        series={[
          {
            label: 'Open',
            data: [times.openCount],
            color: palette.warning.main,
          },
          {
            label: 'Complete',
            data: [times.completeCount],
            color: palette.success.main,
          },
          {
            label: 'Error',
            data: [times.errorCount],
            color: palette.error.main,
          },
        ]}
        slotProps={{ legend: { hidden: true } }}
        width={250}
        height={150}
      />
    </Stack>
  );
}
