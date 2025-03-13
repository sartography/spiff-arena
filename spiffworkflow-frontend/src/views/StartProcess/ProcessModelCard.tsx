import {
  Card,
  Button,
  Stack,
  Typography,
  CardActionArea,
  CardContent,
  CardActions,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { PointerEvent, useEffect, useState } from 'react';
import { Subject, Subscription } from 'rxjs';
import { modifyProcessIdentifierForPathParam } from '../../helpers';
import { getStorageValue } from '../../services/LocalStorageService';
import { ProcessModel } from '../../interfaces';

const defaultStyle = {
  ':hover': {
    backgroundColor: 'background.bluegreylight',
  },
  padding: 2,
  display: 'flex',
  flexDirection: 'column',
  height: '100%',
  position: 'relative',
  border: '1px solid',
  borderColor: 'borders.primary',
  borderRadius: 2,
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
  onStartProcess,
  onViewProcess,
}: {
  model: ProcessModel;
  stream?: Subject<Record<string, any>>;
  lastSelected?: Record<string, any>;
  onStartProcess?: () => void;
  onViewProcess?: () => void;
}) {
  const [selectedStyle, setSelectedStyle] =
    useState<Record<string, any>>(defaultStyle);
  const [isFavorite, setIsFavorite] = useState(false);

  const navigate = useNavigate();

  const stopEventBubble = (e: PointerEvent) => {
    e.stopPropagation();
    e.preventDefault();
  };

  const handleStartProcess = (e: PointerEvent) => {
    stopEventBubble(e);
    if (onStartProcess) {
      onStartProcess();
    }
    const modifiedProcessModelId = modifyProcessIdentifierForPathParam(
      model.id,
    );
    navigate(`/${modifiedProcessModelId}/start`);
  };

  const handleViewProcess = (e: PointerEvent) => {
    stopEventBubble(e);
    if (onViewProcess) {
      onViewProcess();
    }
    const modifiedProcessModelId = modifyProcessIdentifierForPathParam(
      model.id,
    );
    navigate(`/process-models/${modifiedProcessModelId}`);
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
  // const handleFavoriteClick = (e: PointerEvent) => {
  //   stopEventBubble(e);
  //   const currentValue = JSON.parse(getStorageValue('spifffavorites') || '[]');
  //   // Do not set this into state and immediately try to retrieve it.
  //   const favorite = !isFavorite;
  //   setIsFavorite(favorite);
  //   if (favorite) {
  //     // No duplicates
  //     const set: Set<string> = new Set([...currentValue, model.id]);
  //     setStorageValue('spifffavorites', JSON.stringify(Array.from(set)));
  //     return;
  //   }
  //
  //   const removed = currentValue.filter((id: string) => id !== model.id);
  //   setStorageValue('spifffavorites', JSON.stringify(removed));
  // };

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
    <Card
      elevation={0}
      sx={selectedStyle}
      onClick={(e) => handleViewProcess(e as unknown as PointerEvent)}
      id={`card-${modifyProcessIdentifierForPathParam(model.id)}`}
    >
      <CardActionArea>
        <CardContent>
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
          </Stack>
        </CardContent>
      </CardActionArea>
      <CardActions sx={{ mt: 'auto', p: 2 }}>
        <Button
          variant="contained"
          color="primary"
          size="small"
          onClick={(e) => handleStartProcess(e as unknown as PointerEvent)}
        >
          Start this process
        </Button>
      </CardActions>
    </Card>
  );
}
