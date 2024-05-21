import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Paper,
  Stack,
  Typography,
  useTheme,
} from '@mui/material';
import { BarChart, PieChart, SparkLineChart } from '@mui/x-charts';
import { useEffect, useState } from 'react';
import Slider from 'react-slick';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

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

  const sxProps = {
    borderRadius: 1,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    width: '100%',
    height: 200,
    border: '1px solid',
    borderColor: 'divider',
  };

  const breakPoints = [
    {
      breakpoint: 600,
      settings: {
        slidesToShow: 1,
        slidesToScroll: 1,
      },
    },
    {
      breakpoint: 900,
      settings: {
        slidesToShow: 2,
        slidesToScroll: 1,
      },
    },
    {
      breakpoint: 1200,
      settings: {
        slidesToShow: 3,
        slidesToScroll: 1,
      },
    },
    {
      breakpoint: 1500,
      settings: {
        slidesToShow: 4,
        slidesToScroll: 1,
      },
    },
  ];

  return (
    <Accordion defaultExpanded sx={{ boxShadow: 'none', padding: 2 }}>
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        aria-controls="panel1-content"
        id="panel1-header"
      >
        <Typography color="primary">Dashboard KPIs</Typography>
      </AccordionSummary>
      <AccordionDetails>
        <Slider
          dots
          speed={500}
          infinite
          slidesToShow={4}
          center
          responsive={[...breakPoints]}
        >
          <Box sx={{ padding: 1 }}>
            <Paper
              elevation={0}
              sx={{
                ...sxProps,
              }}
            >
              <Stack sx={{ padding: 1 }}>
                <Typography
                  variant="button"
                  sx={{ fontWeight: 600, lineHeight: 1 }}
                >
                  ({times.totalCount}) Processes
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                  Status Distribution
                </Typography>
              </Stack>
              <BarChart
                borderRadius={4}
                skipAnimation
                margin={{
                  left: 20,
                  right: 20,
                  top: 20,
                  bottom: 20,
                }}
                xAxis={[
                  {
                    scaleType: 'band',
                    data: [''],
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
                  {
                    label: 'Total',
                    data: [times.totalCount],
                    color: palette.info.main,
                  },
                ]}
                slotProps={{ legend: { hidden: true } }}
                leftAxis={null}
              />
            </Paper>
          </Box>

          <Box sx={{ padding: 1 }}>
            <Paper elevation={0} sx={{ ...sxProps }}>
              <Stack sx={{ padding: 1 }}>
                <Typography
                  variant="button"
                  sx={{ fontWeight: 600, lineHeight: 1 }}
                >
                  Status Distribution
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                  Milliseconds
                </Typography>
              </Stack>
              <Box
                sx={{
                  width: '100%',
                  height: '100%',
                  padding: 1,
                  display: 'flex',
                  flex: 1,
                  justifyContent: 'center',
                }}
              >
                <PieChart
                  title="Process Instances"
                  sx={{ marginLeft: '40%' }}
                  series={[
                    {
                      data: Object.keys(durations).map(
                        (d: string, i: number) => ({
                          id: i,
                          label: durations[d].displayName,
                          value: durations[d].duration,
                        })
                      ),
                    },
                  ]}
                  slotProps={{ legend: { hidden: true } }}
                />
              </Box>
            </Paper>
          </Box>

          <Box sx={{ padding: 1 }}>
            <Paper elevation={0} sx={{ ...sxProps }}>
              <Stack sx={{ padding: 1 }}>
                <Typography
                  variant="button"
                  sx={{ fontWeight: 600, lineHeight: 1 }}
                >
                  Time Distribution 1
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                  Relative Peaks
                </Typography>
              </Stack>
              <SparkLineChart
                data={Object.keys(durations).map(
                  (d: string) => durations[d].duration
                )}
                curve="natural"
                area
                showHighlight
                showTooltip
              />
            </Paper>
          </Box>

          <Box sx={{ padding: 1 }}>
            <Paper elevation={0} sx={{ ...sxProps }}>
              <Stack sx={{ padding: 1 }}>
                <Typography
                  variant="button"
                  sx={{ fontWeight: 600, lineHeight: 1 }}
                >
                  Time Distribution 2
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                  Absolute Peaks
                </Typography>
              </Stack>
              <BarChart
                borderRadius={4}
                skipAnimation
                margin={{
                  left: 20,
                  right: 20,
                  top: 20,
                  bottom: 20,
                }}
                xAxis={[
                  {
                    scaleType: 'band',
                    data: [''],
                  },
                ]}
                series={Object.keys(durations).map((d: string) => ({
                  label: durations[d].displayName,
                  data: [durations[d].duration],
                }))}
                slotProps={{ legend: { hidden: true } }}
                leftAxis={null}
              />
            </Paper>
          </Box>
        </Slider>
      </AccordionDetails>
    </Accordion>
  );
}
