import { Filter, Link as LinkIcon } from '@carbon/icons-react';
import { Button, Grid, Column } from '@carbon/react';
import { useState } from 'react';
import { Notification } from './Notification';

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

  const [copiedReportLinktoClipboard, setCopiedReportLinkToClipboard] =
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
        <Button
          onClick={copyReportLink}
          kind="secondary"
          renderIcon={LinkIcon}
          iconDescription="Copy shareable link"
          hasIconOnly
          size="md"
        />,
      );
    }
    elements.push(
      <Button
        data-qa="filter-section-expand-toggle"
        renderIcon={Filter}
        iconDescription="Filter Options"
        hasIconOnly
        size="md"
        onClick={toggleShowFilterOptions}
      />,
    );
    if (copiedReportLinktoClipboard) {
      elements.push(
        <Notification
          onClose={() => setCopiedReportLinkToClipboard(false)}
          type="success"
          title="Copied link to clipboard"
          timeout={2000}
          hideCloseButton
          withBottomMargin={false}
        />,
      );
    }
    return elements;
  };

  if (filtersEnabled) {
    let reportSearchSection = null;
    if (reportSearchComponent) {
      reportSearchSection = (
        <Column sm={2} md={6} lg={14}>
          {reportSearchComponent()}
        </Column>
      );
    }
    return (
      <>
        <Grid fullWidth>
          {reportSearchSection}
          <Column
            className="filter-icon"
            sm={{ span: 2, offset: 2 }}
            md={{ span: 2, offset: 6 }}
            lg={{ span: 2, offset: 14 }}
          >
            {buttonElements()}
          </Column>
        </Grid>
        {filterOptions()}
      </>
    );
  }
  return null;
}
