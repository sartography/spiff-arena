import { Box, Paper, Typography, useTheme } from '@mui/material';
import { useEffect, useState } from 'react';
import ArrowDropUpIcon from '@mui/icons-material/ArrowDropUp';
import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown';
import { grey } from '@mui/material/colors';

export default function CollapseButton({
  callback,
  toggle = false,
}: {
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
    console.log(t);
    setToggled(t);
    callback(t);
  };
  return (
    <Paper
      elevation={1}
      sx={{
        width: 50,
        height: 25,
        border: '1px solid',
        borderColor: isDark ? grey[50] : grey[400],
        paddingBottom: 2,
      }}
      onClick={() => handleClick()}
    >
      <Box
        sx={{
          userSelect: 'none',
          textAlign: 'center',
          color: isDark ? grey[50] : grey[600],
        }}
      >
        {toggled ? <ArrowDropDownIcon /> : <ArrowDropUpIcon />}
      </Box>
    </Paper>
  );
}
