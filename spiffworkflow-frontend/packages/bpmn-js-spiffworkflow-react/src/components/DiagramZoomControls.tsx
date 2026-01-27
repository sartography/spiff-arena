import React from 'react';
import { Button, ButtonGroup } from '@mui/material';
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
        <Button
          onClick={onZoomIn}
          startIcon={<ZoomIn fontSize="small" />}
          aria-label={zoomInLabel}
        >
          {zoomInLabel}
        </Button>
        <Button
          onClick={onZoomOut}
          startIcon={<ZoomOut fontSize="small" />}
          aria-label={zoomOutLabel}
        >
          {zoomOutLabel}
        </Button>
        <Button
          onClick={onZoomFit}
          startIcon={<CenterFocusStrongOutlined fontSize="small" />}
          aria-label={zoomFitLabel}
        >
          {zoomFitLabel}
        </Button>
      </ButtonGroup>
    </div>
  );
}
