// @ts-ignore
import { Filter } from '@carbon/icons-react';
import {
  Button,
  Grid,
  Column,
  // @ts-ignore
} from '@carbon/react';

type OwnProps = {
  showFilterOptions: boolean;
  setShowFilterOptions: Function;
  filterOptions: Function;
  filtersEnabled?: boolean;
  reportSearchComponent?: Function | null;
};

export default function Filters({
  showFilterOptions,
  setShowFilterOptions,
  filterOptions,
  reportSearchComponent = null,
  filtersEnabled = true,
}: OwnProps) {
  const toggleShowFilterOptions = () => {
    setShowFilterOptions(!showFilterOptions);
  };

  if (filtersEnabled) {
    let reportSearchSection = null;
    if (reportSearchComponent) {
      reportSearchSection = (
        <Column sm={3} md={7} lg={15}>
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
            sm={{ span: 1, offset: 3 }}
            md={{ span: 1, offset: 7 }}
            lg={{ span: 1, offset: 15 }}
          >
            <Button
              data-qa="filter-section-expand-toggle"
              renderIcon={Filter}
              iconDescription="Filter Options"
              hasIconOnly
              size="md"
              onClick={toggleShowFilterOptions}
            />
          </Column>
        </Grid>
        {filterOptions()}
      </>
    );
  }
  return null;
}
