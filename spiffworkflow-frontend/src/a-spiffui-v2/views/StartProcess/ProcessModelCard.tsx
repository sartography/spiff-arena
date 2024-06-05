import { Button, Paper, Stack, Typography } from '@mui/material';
import { useEffect, useState } from 'react';
import { Subject, Subscription } from 'rxjs';

const defaultStyle = {
  borderRadius: 2,
  padding: 2,
  margin: 2,
  borderWidth: 1,
  borderStyle: 'solid',
  borderColor: 'borders.primary',
  minWidth: 320,
};

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
  const captionColor = 'text.secondary';

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
   * Interesting one; when a group loads, it could be because the user
   * clicked a model in a "non active" group in the tree,
   * which we then expand the parent group and load the cards.
   * This means there's no clickstream data to highlight the newly loaded card.
   * So, on init (and only once), we check if this is the lastSelected model,
   * if yes, highlight it.
   */
  let styleInit = false;
  useEffect(() => {
    if (!styleInit && lastSelected) {
      handleClickStream(lastSelected);
      styleInit = true;
    }
  }, [lastSelected]);

  let streamSub: Subscription;
  useEffect(() => {
    if (!streamSub && stream) {
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
      <Stack>
        <Typography variant="body2" sx={{ fontWeight: 700 }}>
          {model.display_name}
        </Typography>
        <Typography variant="body2" sx={{ fontWeight: 700 }}>
          {model.description || '--'}
        </Typography>

        <Typography variant="caption" sx={{ color: captionColor }}>
          ID: {model.id}
        </Typography>

        <Stack direction="row" sx={{ paddingTop: 2 }}>
          <Button variant="contained" color="primary" size="small">
            Start This Process
          </Button>
        </Stack>
      </Stack>
    </Paper>
  );
}
