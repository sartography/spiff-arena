import React from 'react';
import { Button, ButtonGroup, Tooltip } from '@mui/material';
import {
  CenterFocusStrongOutlined,
  ZoomIn,
  ZoomOut,
} from '@mui/icons-material';

type DiagramZoomControlsProps = {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onZoomFit: () => void;
  zoomInLabel: string;
  zoomOutLabel: string;
  zoomFitLabel: string;
};

export default function DiagramZoomControls({
  onZoomIn,
  onZoomOut,
  onZoomFit,
  zoomInLabel,
  zoomOutLabel,
  zoomFitLabel,
}: DiagramZoomControlsProps) {
  return (
    <div className="diagram-zoom-controls">
      <ButtonGroup variant="outlined" size="small" aria-label="Diagram zoom">
        <Tooltip title={zoomInLabel}>
          <Button
            onClick={onZoomIn}
            aria-label={zoomInLabel}
          >
            <ZoomIn fontSize="small" />
          </Button>
        </Tooltip>
        <Tooltip title={zoomOutLabel}>
          <Button
            onClick={onZoomOut}
            aria-label={zoomOutLabel}
          >
            <ZoomOut fontSize="small" />
          </Button>
        </Tooltip>
        <Tooltip title={zoomFitLabel}>
          <Button
            onClick={onZoomFit}
            aria-label={zoomFitLabel}
          >
            <CenterFocusStrongOutlined fontSize="small" />
          </Button>
        </Tooltip>
      </ButtonGroup>
    </div>
  );
}
