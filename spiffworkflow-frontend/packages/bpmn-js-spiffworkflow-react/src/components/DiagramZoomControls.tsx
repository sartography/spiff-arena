import React from 'react';
import { IconButton, Tooltip } from '@mui/material';
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
    <div className="diagram-control-buttons">
      <Tooltip title={zoomInLabel} placement="bottom">
        <IconButton aria-label={zoomInLabel} onClick={onZoomIn}>
          <ZoomIn />
        </IconButton>
      </Tooltip>
      <Tooltip title={zoomOutLabel} placement="bottom">
        <IconButton aria-label={zoomOutLabel} onClick={onZoomOut}>
          <ZoomOut />
        </IconButton>
      </Tooltip>
      <Tooltip title={zoomFitLabel} placement="bottom">
        <IconButton aria-label={zoomFitLabel} onClick={onZoomFit}>
          <CenterFocusStrongOutlined />
        </IconButton>
      </Tooltip>
    </div>
  );
}
