import React from 'react';
import { Breadcrumbs, Chip, Link } from '@mui/material';
import type { DiagramNavigationItem } from '../hooks/useDiagramNavigationStack';

type DiagramNavigationBreadcrumbsProps = {
  stack: DiagramNavigationItem[];
  onNavigate: (index: number) => void;
  getLabel?: (item: DiagramNavigationItem) => string;
};

export default function DiagramNavigationBreadcrumbs({
  stack,
  onNavigate,
  getLabel,
}: DiagramNavigationBreadcrumbsProps) {
  const labelFor = (item: DiagramNavigationItem) =>
    getLabel?.(item) ||
    item.displayName ||
    item.fileName ||
    item.processModelId;

  if (stack.length === 0) {
    return null;
  }

  return (
    <Breadcrumbs aria-label="diagram-navigation">
      {stack.map((item, index) => {
        const isLast = index === stack.length - 1;
        const label = labelFor(item);

        if (isLast) {
          return <Chip key={`${item.processModelId}-${item.fileName}`} label={label} color="primary" size="small" />;
        }

        return (
          <Link
            key={`${item.processModelId}-${item.fileName}`}
            component="button"
            variant="body2"
            onClick={() => onNavigate(index)}
            sx={{
              cursor: 'pointer',
              textDecoration: 'none',
              '&:hover': { textDecoration: 'underline' },
            }}
          >
            {label}
          </Link>
        );
      })}
    </Breadcrumbs>
  );
}
