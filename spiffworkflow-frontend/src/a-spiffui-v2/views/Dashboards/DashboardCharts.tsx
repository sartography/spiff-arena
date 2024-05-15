import { Stack, useTheme } from '@mui/material';
import {
  BarChart,
  PieChart,
  SparkLineChart,
  ScatterChart,
} from '@mui/x-charts';
import { useEffect, useState } from 'react';

export default function DashboardCharts({
  times,
}: {
  times: Record<string, any>;
}) {
  const [durations, setDurations] = useState<Record<string, any>>({});
  const { palette } = useTheme();

  useEffect(() => {
    if (Object.keys(times).length === 0) {
      return;
    }

    const totalDurations: Record<string, any> = {};
    Object.keys(times.summary).forEach((key) => {
      totalDurations[key] = {
        duration: times.summary[key].times.reduce(
          (acc: number, curr: Record<string, any>) => acc + curr.duration,
          0
        ),
        displayName: times.summary[key].displayName,
      };
    });
    setDurations(totalDurations);
  }, [times]);

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
        leftAxis={null}
      />

      <PieChart
        title="Time Distribution"
        series={[
          {
            data: Object.keys(durations).map((d: string, i: number) => ({
              id: i,
              label: durations[d].displayName,
              value: durations[d].duration,
            })),
          },
        ]}
        slotProps={{ legend: { hidden: true } }}
        width={250}
        height={150}
        margin={{
          left: 50,
          right: 0,
          top: 20,
          bottom: 20,
        }}
      />

      <SparkLineChart
        data={Object.keys(durations).map((d: string) => durations[d].duration)}
        margin={{
          left: 50,
          right: 0,
          top: 20,
          bottom: 20,
        }}
        height={150}
        width={250}
        curve="natural"
        area
        showHighlight
        showTooltip
      />

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
            data: ['Duration Distribution'],
          },
        ]}
        series={Object.keys(durations).map((d: string) => ({
          label: durations[d].displayName,
          data: [durations[d].duration],
        }))}
        slotProps={{ legend: { hidden: true } }}
        width={250}
        height={150}
        leftAxis={null}
      />
    </Stack>
  );
}
