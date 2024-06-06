import { Paper, Stack, useTheme } from '@mui/material';
import { useEffect, useState } from 'react';
import ArrowRightIcon from '@mui/icons-material/ArrowRight';
import ArrowLeftIcon from '@mui/icons-material/ArrowLeft';
import { grey } from '@mui/material/colors';

export default function CollapseButton({
  startDirection,
  callback,
  toggle = false,
}: {
  startDirection: 'left' | 'right';
  callback: (data: boolean) => void;
  toggle?: boolean;
}) {
  const [toggled, setToggled] = useState(false);

  const isDark = useTheme().palette.mode === 'dark';

  useEffect(() => {
    // Dev can reset toggle if they need
    setToggled(toggle);
  }, [toggle]);

  const handleClick = () => {
    // You can run into async state update issues if you
    // try to use the state value directly in the callback.
    const t = !toggled;
    setToggled(t);
    callback(t);
  };
  return (
    <Paper
      elevation={1}
      sx={{
        width: 25,
        height: 50,
        border: '1px solid',
        borderColor: 'borders.primary',
        backgroundColor: 'background.paper',
      }}
      onClick={() => handleClick()}
    >
      <Stack
        sx={{
          textAlign: 'center',
          color: isDark ? grey[50] : grey[600],
          height: '100%',
          justifyContent: 'center',
        }}
      >
        {startDirection === 'right' &&
          (toggled ? <ArrowLeftIcon /> : <ArrowRightIcon />)}
        {startDirection === 'left' &&
          (toggled ? <ArrowRightIcon /> : <ArrowLeftIcon />)}
      </Stack>
    </Paper>
  );
}
