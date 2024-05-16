import { Paper, Typography, useTheme } from '@mui/material';
import { useEffect, useState } from 'react';

export default function CollapseButton({
  callback,
  toggle = false,
}: {
  callback: (data: boolean) => void;
  toggle?: boolean;
}) {
  const [toggled, setToggled] = useState(false);

  useEffect(() => {
    // Dev can reset toggle if they need
    setToggled(toggle);
  }, [toggle]);

  const handleClick = () => {
    // You can run into async state update issues if you
    // try to use the state value directly in the callback.
    const t = !toggled;
    console.log(t);
    setToggled(t);
    callback(t);
  };
  return (
    <Paper
      elevation={1}
      sx={{
        padding: 1,
        borderRadius: '50%',
        width: 50,
        height: 50,
        border: '1px solid',
        borderColor: `primary.${useTheme().palette.mode}`,
      }}
      onClick={() => handleClick()}
    >
      <Typography variant="h5" textAlign="center" sx={{ userSelect: 'none' }}>
        {toggled ? '>' : '<'}
      </Typography>
    </Paper>
  );
}
