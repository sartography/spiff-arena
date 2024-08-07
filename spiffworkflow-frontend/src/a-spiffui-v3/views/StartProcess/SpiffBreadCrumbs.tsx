import { Box, Stack, Typography } from '@mui/material';

/**
 * Used to display a breadcrumb UI to facilitate card navigation.
 * Breadcrumbs are derived from the id of the currently selected group or model.
 * We also need to mask each crumb with the item's display name.
 * Updates whenever the clickstream receives a new group or model object.
 */

const crumbStyle = {
  backgroundColor: 'background.bluegreymedium',
  paddingLeft: 1,
  paddingRight: 1,
  borderRadius: 1,
  cursor: 'pointer',
  '&:hover': {
    textDecoration: 'underline',
  },
};

export const SPIFF_ID = 'spifftop';
export type Crumb = { id: string; displayName: string };
export default function SpiffBreadCrumbs({
  crumbs,
  callback,
}: {
  crumbs: Crumb[];
  callback: (crumb: Crumb) => void;
}) {
  return (
    <Stack direction="row" gap={1}>
      <Box
        key={SPIFF_ID}
        onClick={() => callback({ id: SPIFF_ID, displayName: 'Root' })}
        sx={crumbStyle}
      >
        <Typography key={SPIFF_ID} variant="caption">
          Root
        </Typography>
      </Box>
      {crumbs &&
        crumbs.map((crumb) => (
          // Crumbs are built from a Set, there should be no duplicates
          <Box key={crumb.id} onClick={() => callback(crumb)} sx={crumbStyle}>
            <Typography key={crumb.id} variant="caption">
              {crumb.displayName}
            </Typography>
          </Box>
        ))}
    </Stack>
  );
}
