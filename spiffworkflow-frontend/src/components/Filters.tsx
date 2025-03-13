import {
  FilterAlt as FilterAltIcon,
  Link as LinkIcon,
} from '@mui/icons-material';
import { Grid, IconButton, Snackbar } from '@mui/material';
import { useState } from 'react';
import SpiffTooltip from './SpiffTooltip';

type OwnProps = {
  showFilterOptions: boolean;
  setShowFilterOptions: Function;
  filterOptions: Function;
  filtersEnabled?: boolean;
  reportSearchComponent?: Function | null;
  reportHash?: string | null;
};

export default function Filters({
  showFilterOptions,
  setShowFilterOptions,
  filterOptions,
  reportSearchComponent = null,
  filtersEnabled = true,
  reportHash,
}: OwnProps) {
  const toggleShowFilterOptions = () => {
    setShowFilterOptions(!showFilterOptions);
  };

  const [copiedReportLinkToClipboard, setCopiedReportLinkToClipboard] =
    useState<boolean>(false);

  const copyReportLink = () => {
    if (reportHash) {
      const piShortLink = `${window.location.origin}${window.location.pathname}?report_hash=${reportHash}`;
      navigator.clipboard.writeText(piShortLink);
      setCopiedReportLinkToClipboard(true);
    }
  };

  const buttonElements = () => {
    const elements = [];
    if (reportHash && showFilterOptions) {
      elements.push(
        <SpiffTooltip title="Copy shareable link">
          <IconButton
            onClick={copyReportLink}
            color="primary"
            aria-label="Copy shareable link"
          >
            <LinkIcon />
          </IconButton>
        </SpiffTooltip>,
      );
    }
    elements.push(
      <SpiffTooltip title="Filter Options">
        <IconButton
          data-qa="filter-section-expand-toggle"
          color="primary"
          aria-label="Filter Options"
          onClick={toggleShowFilterOptions}
        >
          <FilterAltIcon />
        </IconButton>
      </SpiffTooltip>,
    );
    if (copiedReportLinkToClipboard) {
      elements.push(
        <Snackbar
          open={copiedReportLinkToClipboard}
          autoHideDuration={2000}
          onClose={() => setCopiedReportLinkToClipboard(false)}
          message="Copied link to clipboard"
        />,
      );
    }
    return elements;
  };

  if (filtersEnabled) {
    let reportSearchSection = null;
    if (reportSearchComponent) {
      reportSearchSection = (
        <Grid item xs={12} sm={6} md={8}>
          {reportSearchComponent()}
        </Grid>
      );
    }
    return (
      <>
        <Grid
          container
          spacing={2}
          style={{ paddingBottom: '1rem' }}
          justifyContent="flex-end"
        >
          {reportSearchSection}
          <Grid item xs={12} sm={6} md={4} className="filter-icon">
            {buttonElements()}
          </Grid>
        </Grid>
        {filterOptions()}
      </>
    );
  }
  return null;
}
