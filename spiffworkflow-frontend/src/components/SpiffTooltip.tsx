// carbon shifts everything but mui doesn't
// import { Tooltip } from '@carbon/react';

import { Tooltip } from '@mui/material';
import { ReactElement } from 'react';

interface OwnProps {
  title?: string;
  placement?: 'top' | 'bottom' | 'left' | 'right';
  children: ReactElement;
}

export default function SpiffTooltip({ title, children, placement }: OwnProps) {
  //
  return (
    <Tooltip
      title={title}
      arrow
      enterDelay={500}
      // eslint-disable-next-line react/jsx-props-no-spreading
      {...(placement ? { placement } : {})}
      PopperProps={{ style: { zIndex: 9999 } }}
    >
      {children}
    </Tooltip>
  );
}
