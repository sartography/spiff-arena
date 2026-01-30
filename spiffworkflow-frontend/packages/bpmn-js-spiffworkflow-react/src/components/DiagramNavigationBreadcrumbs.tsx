import React, { useState, MouseEvent } from 'react';
import { Breadcrumbs, Chip, Link, Menu, MenuItem, ListItemIcon, ListItemText } from '@mui/material';
import { Download, Code, ExpandMore } from '@mui/icons-material';
import type { DiagramNavigationItem } from '../hooks/useDiagramNavigationStack';

type DiagramNavigationBreadcrumbsProps = {
  stack: DiagramNavigationItem[];
  onNavigate: (index: number) => void;
  getLabel?: (item: DiagramNavigationItem) => string;
  onDownload?: () => void;
  onViewXml?: () => void;
  canDownload?: boolean;
  canViewXml?: boolean;
  downloadLabel?: string;
  viewXmlLabel?: string;
};

export default function DiagramNavigationBreadcrumbs({
  stack,
  onNavigate,
  getLabel,
  onDownload,
  onViewXml,
  canDownload,
  canViewXml,
  downloadLabel,
  viewXmlLabel,
}: DiagramNavigationBreadcrumbsProps) {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const handleMenuClick = (event: MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleDownload = () => {
    onDownload?.();
    handleMenuClose();
  };

  const handleViewXml = () => {
    onViewXml?.();
    handleMenuClose();
  };

  const labelFor = (item: DiagramNavigationItem) =>
    getLabel?.(item) ||
    item.displayName ||
    item.fileName ||
    item.modifiedProcessModelId;

  if (stack.length === 0) {
    return null;
  }

  return (
    <Breadcrumbs
      aria-label="diagram-navigation"
      className="spiff-breadcrumb"
      sx={{
        mb: '0 !important',
        display: 'flex',
        alignItems: 'center',
        '& .MuiBreadcrumbs-ol': {
          alignItems: 'center',
          m: 0,
          p: 0,
          display: 'flex',
        },
      }}
    >
      {stack.map((item, index) => {
        const isLast = index === stack.length - 1;
        const label = labelFor(item);

        if (isLast) {
          const hasActions = (canDownload && onDownload) || (canViewXml && onViewXml);
          return (
            <React.Fragment key={`${item.modifiedProcessModelId}-${item.fileName}`}>
              <Chip
                label={label}
                color="primary"
                size="small"
                onClick={hasActions ? handleMenuClick : undefined}
                onDelete={hasActions ? handleMenuClick : undefined}
                deleteIcon={hasActions ? <ExpandMore /> : undefined}
                data-testid="diagram-file-chip"
                sx={{
                  '& .MuiChip-deleteIcon': {
                    color: 'inherit',
                  },
                }}
              />
              {hasActions && (
                <Menu
                  anchorEl={anchorEl}
                  open={open}
                  onClose={handleMenuClose}
                >
                  {canDownload && onDownload && (
                    <MenuItem onClick={handleDownload}>
                      <ListItemIcon>
                        <Download fontSize="small" />
                      </ListItemIcon>
                      <ListItemText>{downloadLabel || 'Download'}</ListItemText>
                    </MenuItem>
                  )}
                  {canViewXml && onViewXml && (
                    <MenuItem onClick={handleViewXml}>
                      <ListItemIcon>
                        <Code fontSize="small" />
                      </ListItemIcon>
                      <ListItemText>{viewXmlLabel || 'View XML'}</ListItemText>
                    </MenuItem>
                  )}
                </Menu>
              )}
            </React.Fragment>
          );
        }

        return (
          <Link
            key={`${item.modifiedProcessModelId}-${item.fileName}`}
            component="button"
            variant="body2"
            underline="none"
            onClick={() => onNavigate(index)}
            sx={{
              cursor: 'pointer',
            }}
          >
            {label}
          </Link>
        );
      })}
    </Breadcrumbs>
  );
}
