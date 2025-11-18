import {
  FilterAlt as FilterAltIcon,
  Link as LinkIcon,
} from '@mui/icons-material';
import Grid from '@mui/material/Grid';
import { IconButton, Snackbar } from '@mui/material';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
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

  const { t } = useTranslation();
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
        <SpiffTooltip title={t('copy_shareable_link')}>
          <IconButton
            onClick={copyReportLink}
            color="primary"
            aria-label={t('copy_shareable_link')}
          >
            <LinkIcon />
          </IconButton>
        </SpiffTooltip>,
      );
    }
    elements.push(
      <SpiffTooltip title={t('filter_options')}>
        <IconButton
          data-testid="filter-section-expand-toggle"
          color="primary"
          aria-label={t('filter_options')}
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
          message={t('copied_link_to_clipboard')}
        />,
      );
    }
    return elements;
  };

  if (filtersEnabled) {
    let reportSearchSection = null;
    if (reportSearchComponent) {
      reportSearchSection = (
        <Grid size={{ xs: 12, sm: 6, md: 8 }}>
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
          <Grid size={{ xs: 12, sm: 6, md: 4 }} className="filter-icon">
            {buttonElements()}
          </Grid>
        </Grid>
        {filterOptions()}
      </>
    );
  }
  return null;
}
