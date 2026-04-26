import React from 'react';
import { Dialog, List, ListItem, ListItemText, Link, Box } from '@mui/material';
import type { ProcessReference } from '../types';

type ProcessReferencesDialogProps = {
  open: boolean;
  onClose: () => void;
  title: string;
  references: ProcessReference[];
  buildHref: (reference: ProcessReference) => string;
};

export default function ProcessReferencesDialog({
  open,
  onClose,
  title,
  references,
  buildHref,
}: ProcessReferencesDialogProps) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      aria-labelledby="process-references-title"
    >
      <Box sx={{ p: 4 }}>
        <h2 id="process-references-title">{title}</h2>
        <List>
          {references.map((ref) => (
            <ListItem key={ref.relative_location} disableGutters>
              <ListItemText
                primary={
                  <Link href={buildHref(ref)}>{ref.display_name}</Link>
                }
                secondary={ref.relative_location}
              />
            </ListItem>
          ))}
        </List>
      </Box>
    </Dialog>
  );
}
