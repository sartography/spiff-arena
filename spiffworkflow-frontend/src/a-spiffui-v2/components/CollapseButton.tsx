import { Paper, Stack } from '@mui/material';
import { useEffect, useState } from 'react';
import ArrowRightIcon from '@mui/icons-material/ArrowRight';
import ArrowLeftIcon from '@mui/icons-material/ArrowLeft';

/** A button-ish widget that can be used as a collapse button for any container */
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

  useEffect(() => {
    // Dev can reset toggle if they need
    setToggled(toggle);
  }, [toggle]);

  const handleClick = () => {
    // Don't set set and then immediately try to retrieve the value
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
          color: 'text.subheading',
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
