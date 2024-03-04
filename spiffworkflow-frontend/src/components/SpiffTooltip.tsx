// carbon shifts everything but mui doesn't
// import { Tooltip } from '@carbon/react';

import { Tooltip } from '@mui/material';
import { ReactElement } from 'react';

interface OwnProps {
  title?: string;
  children: ReactElement;
}

export default function SpiffTooltip({ title, children }: OwnProps) {
  return (
    <Tooltip
      title={title}
      arrow
      enterDelay={500}
      PopperProps={{ style: { zIndex: 9999 } }}
    >
      {children}
    </Tooltip>
  );
}
