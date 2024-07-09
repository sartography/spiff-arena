import { Box, Button, Paper, Stack, Typography } from '@mui/material';
import { PointerEvent, useEffect, useState } from 'react';
import { Subject, Subscription } from 'rxjs';
import StarRateIcon from '@mui/icons-material/StarRate';
import StarBorderOutlinedIcon from '@mui/icons-material/StarBorderOutlined';
import {
  getStorageValue,
  setStorageValue,
} from '../../services/LocalStorageService';

const defaultStyle = {
  borderRadius: 2,
  padding: 2,
  margin: 2,
  borderWidth: 1,
  borderStyle: 'solid',
  borderColor: 'borders.primary',
  minWidth: 320,
  position: 'relative',
  ':hover': {
    backgroundColor: 'background.bluegreylight',
  },
};

/**
 * Displays the Process Model info.
 * Note that Models and Groups may seem similar, but
 * some of the event handling and stream info is different.
 * Eventually might refactor to a common component, but at this time
 * it's useful to keep them separate.
 */
export default function ProcessModelCard({
  model,
  stream,
  lastSelected,
}: {
  model: Record<string, any>;
  stream?: Subject<Record<string, any>>;
  lastSelected?: Record<string, any>;
}) {
  const [selectedStyle, setSelectedStyle] =
    useState<Record<string, any>>(defaultStyle);
  const [isFavorite, setIsFavorite] = useState(false);

  const stopEventBubble = (e: PointerEvent) => {
    e.stopPropagation();
    e.preventDefault();
  };

  const handleClickStream = (item: Record<string, any>) => {
    if (model.id === item.id) {
      setSelectedStyle((prev) => ({
        ...prev,
        borderColor: 'primary.main',
        borderWidth: 2,
        boxShadow: 2,
      }));

      return;
    }

    setSelectedStyle({ ...defaultStyle });
  };

  /**
   * If this becomes a favorite, add to localstorage list and return,
   * otherwise remove.
   */
  const handleFavoriteClick = (e: PointerEvent) => {
    stopEventBubble(e);
    const currentValue = JSON.parse(getStorageValue('spifffavorites') || '[]');
    // Do not set this into state and immediately try to retrieve it.
    const favorite = !isFavorite;
    setIsFavorite(favorite);
    if (favorite) {
      // No duplicates
      const set: Set<string> = new Set([...currentValue, model.id]);
      setStorageValue('spifffavorites', JSON.stringify(Array.from(set)));
      return;
    }

    const removed = currentValue.filter((id: string) => id !== model.id);
    setStorageValue('spifffavorites', JSON.stringify(removed));
  };

  const handleStartProcess = (e: PointerEvent) => {
    stopEventBubble(e);
  };

  useEffect(() => {
    const favorites = JSON.parse(getStorageValue('spifffavorites'));
    setIsFavorite(favorites.includes(model.id));
  }, [isFavorite, model]);

  /**
   * Interesting one; when a group loads, it could be because the user
   * clicked a model in a "non active" group in the tree. We claer the cards,
   * expand the parent group of that selected model, and load the cards.
   * By the time the cards are loaded, the clickstream that initiated the switch is past.
   * So, pass in the last selected object from the tree,
   * and on init (and only once), we check if this is the lastSelected model,
   * if yes, highlight it.
   */
  let styleInit = false;
  useEffect(() => {
    if (!styleInit && lastSelected) {
      handleClickStream(lastSelected);
      // eslint-disable-next-line react-hooks/exhaustive-deps
      styleInit = true;
    }
  }, [lastSelected]);

  let streamSub: Subscription;
  useEffect(() => {
    if (!streamSub && stream) {
      // eslint-disable-next-line react-hooks/exhaustive-deps
      streamSub = stream.subscribe(handleClickStream);
    }

    return () => {
      streamSub.unsubscribe();
    };
  }, [stream, selectedStyle]);
  return (
    <Paper
      elevation={0}
      sx={selectedStyle}
      onClick={() => stream && stream.next(model)}
    >
      <Box
        sx={{ position: 'absolute', right: 8, top: 8 }}
        onClick={(e) => handleFavoriteClick(e as unknown as PointerEvent)}
      >
        {isFavorite ? (
          <StarRateIcon
            sx={{
              color: 'spotColors.goldStar',
            }}
          />
        ) : (
          <StarBorderOutlinedIcon />
        )}
      </Box>
      <Stack gap={1} sx={{ height: '100%' }}>
        <Typography variant="body2" sx={{ fontWeight: 700 }}>
          {model.display_name}
        </Typography>
        <Typography
          variant="caption"
          sx={{ fontWeight: 700, color: 'text.secondary' }}
        >
          {model.description || '--'}
        </Typography>

        <Stack
          sx={{
            paddingTop: 2,
            width: 150,
            height: '100%',
            justifyContent: 'flex-end',
          }}
        >
          <Button
            variant="contained"
            color="primary"
            size="small"
            onClick={(e) => handleStartProcess(e as unknown as PointerEvent)}
          >
            Start This Process
          </Button>
        </Stack>
      </Stack>
    </Paper>
  );
}
