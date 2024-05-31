import { Button, useTheme } from '@mui/material';
import { blueGrey, grey } from '@mui/material/colors';
import { ReactNode, useEffect, useState } from 'react';
import { Subject, Subscription } from 'rxjs';

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
  path: string;
  icon?: ReactNode;
  toggleData?: ToggleData;
};
export default function MenuItem({
  data,
  callback,
  stream,
}: {
  data: MenuItemData;
  callback: (arg: MenuItemData) => void;
  stream: Subject<MenuItemData>;
}) {
  const [toggled, setToggled] = useState(false);
  const isDark = useTheme().palette.mode === 'dark';
  const palette: any = useTheme().palette;

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

  let subMenuItem: Subscription;
  useEffect(() => {
    if (!subMenuItem) {
      subMenuItem = stream.subscribe((item) => console.log(item));
    }
  }, [stream]);

  /** When given to a pseudo or pre-post class (like :hover), looks like tokens don't work */
  return (
    <Button
      onClick={handleClick}
      startIcon={data.icon}
      sx={{
        minWidth: 125,
        borderColor: isDark ? 'primary' : 'background.mediumdark',
        borderWidth: 1,
        borderStyle: toggled ? 'solid' : 'transparent',
        color: isDark ? 'primary.light' : 'background.darker',
        ':hover': {
          backgroundColor: isDark ? grey[800] : blueGrey[100],
        },
      }}
    >
      {data.text}
    </Button>
  );
}
