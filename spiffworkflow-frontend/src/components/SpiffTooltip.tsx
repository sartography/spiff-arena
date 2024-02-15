// carbon shifts everything but mui doesn't
// import { Tooltip } from '@carbon/react';

import { Tooltip } from '@mui/material';

export default function SpiffTooltip(props: any) {
  const { title, children } = props;
  return (
    <Tooltip title={title} arrow>
      {children}
    </Tooltip>
  );
}
