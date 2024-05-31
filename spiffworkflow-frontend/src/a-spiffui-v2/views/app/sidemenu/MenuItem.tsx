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

  /**
   * Report back toggle state and icon/text if set.
   * Don't set toggled here, that is handled by the stream callback.
   */
  const handleClick = () => {
    const payload = {
      ...data,
      toggleData: {
        ...(data.toggleData || {}),
        toggled: !data.toggleData?.toggled,
      },
    };
    callback(payload);
  };

  /**
   * When any button in the menu is clicked, all of them know which one.
   * We can turn styles on and off, etc. to highlight selected.
   */
  let subMenuItem: Subscription;
  useEffect(() => {
    if (!subMenuItem) {
      subMenuItem = stream.subscribe((item) =>
        setToggled(item.text === data.text)
      );
    }
  }, [stream]);

  /**
   * If the user navigates to this page without clicking buttons (e.g. types the url or bookmark)
   * we need to be aware of that and set the toggled state accordingly.
   */
  useEffect(() => {
    setToggled(window.location.href.indexOf(data.path) > -1);
  }, [data.path]);

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
