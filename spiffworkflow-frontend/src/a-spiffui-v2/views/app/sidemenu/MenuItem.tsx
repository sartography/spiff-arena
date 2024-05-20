import { Stack, Typography, useTheme } from '@mui/material';
import { blueGrey, grey, purple } from '@mui/material/colors';
import { ReactNode, useEffect, useState } from 'react';

/**
 * MenuItem component that satisfies design requirements.
 * Toggle feature: can set a toggleIcon and toggleText,
 * settable toggle state, and writes the info to the callback object.
 */
type ToggleData = {
  toggled: boolean;
  toggleIcon?: ReactNode;
  toggleText?: string;
};
export type MenuItemData = {
  text: string;
  icon: ReactNode;
  path: string;
  toggleData?: ToggleData;
};
export default function MenuItem({
  data,
  callback,
}: {
  data: MenuItemData;
  callback: (arg: MenuItemData) => void;
}) {
  const [toggled, setToggled] = useState(false);
  const isDark = useTheme().palette.mode === 'dark';

  /**
   * Report back toggle state and icon/text if set.
   */
  const handleClick = () => {
    const payload = {
      ...data,
      toggleData: {
        ...(data.toggleData || {}),
        toggled: !data.toggleData?.toggled,
      },
    };
    setToggled((curr) => !curr);
    callback(payload);
  };

  /** If the initial toggle state is set to true, process it.  */
  useEffect(() => {
    if (data.toggleData?.toggled) {
      handleClick();
    }
  }, []);

  return (
    <Stack
      direction="row"
      sx={{
        borderRadius: 5,
        gap: 1,
        padding: 1,
        ':hover': {
          backgroundColor: isDark ? blueGrey[800] : blueGrey[50],
        },
        cursor: 'default',
        alignItems: 'center',
        maxHeight: 40,
      }}
      onClick={() => handleClick()}
    >
      <Typography>
        {data.toggleData && data.toggleData.toggleIcon && toggled
          ? data.toggleData.toggleIcon
          : data.icon}
      </Typography>
      <Typography
        sx={{
          color: isDark ? grey[50] : grey[800],
          fontSize: 13,
          paddingBottom: 0.5,
        }}
      >
        {data.toggleData && data.toggleData.toggleText && toggled
          ? data.toggleData.toggleText
          : data.text}
      </Typography>
    </Stack>
  );
}
