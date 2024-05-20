import { Button, useTheme } from '@mui/material';
import { grey } from '@mui/material/colors';
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
  }, [data]);

  return (
    <Button
      onClick={handleClick}
      startIcon={data.icon}
      sx={{
        borderColor: isDark ? 'primary' : grey[400],
        borderWidth: 1,
        borderStyle: toggled ? 'solid' : 'transparent',
        color: isDark ? 'primary.light' : grey[700],
        ':hover': {
          backgroundColor: isDark ? grey[800] : grey[200],
        },
      }}
    >
      {data.text}
    </Button>
  );
}
