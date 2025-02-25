import { Button, Stack, useTheme } from '@mui/material';
import { grey } from '@mui/material/colors';
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
  align?: 'flex-start' | 'center' | 'flex-end';
};
export default function MenuItem({
  data,
  callback,
  stream,
}: {
  data: MenuItemData;
  callback: (arg: MenuItemData) => void;
  stream?: Subject<MenuItemData>;
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
    if (!subMenuItem && stream) {
      // eslint-disable-next-line react-hooks/exhaustive-deps
      subMenuItem = stream.subscribe((item) =>
        setToggled(item.text === data.text),
      );
    }
  }, [stream]);

  /**
   * If the user navigates to this page without clicking buttons (e.g. types the url or bookmark)
   * we need to be aware of that and set the toggled state accordingly.
   * If no path is set in the data, this check won't run.
   */
  useEffect(() => {
    if (data.path) {
      setToggled(window.location.href.indexOf(data.path) > -1);
    }
  }, [data.path]);

  return (
    <Button
      onClick={handleClick}
      startIcon={data.icon}
      sx={{
        minWidth: 125,
        width: '100%',
        borderColor: isDark ? 'primary' : 'background.mediumdark',
        borderBottomWidth: 1,
        borderRadius: toggled ? 0 : 1,
        fontSize: 12,
        borderStyle: toggled ? 'solid' : 'transparent',
        justifyContent: data?.align || 'center',
        color: isDark ? 'primary.light' : 'text.secondary',
        /** When given to a pseudo or pre-post class (like :hover), looks like tokens don't work */
        ':hover': {
          backgroundColor: isDark ? grey[800] : grey[300],
        },
      }}
    >
      <Stack sx={{ height: '100%', justifyContent: 'center' }}>
        {data.text}
      </Stack>
    </Button>
  );
}
