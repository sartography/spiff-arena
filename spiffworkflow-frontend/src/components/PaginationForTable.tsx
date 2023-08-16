import { useSearchParams } from 'react-router-dom';

// @ts-ignore
import { Pagination } from '@carbon/react';
import { PaginationObject } from '../interfaces';

type OwnProps = {
  page: number;
  perPage: number;
  perPageOptions?: number[];
  pagination: PaginationObject | null;
  tableToDisplay: any;
  paginationQueryParamPrefix?: string;
  paginationClassName?: string;
  paginationDataQATag?: string;
};

export default function PaginationForTable({
  page,
  perPage,
  perPageOptions,
  pagination,
  tableToDisplay,
  paginationQueryParamPrefix,
  paginationClassName,
  paginationDataQATag = 'pagination-options',
}: OwnProps) {
  const PER_PAGE_OPTIONS = [2, 10, 50, 100];
  const [searchParams, setSearchParams] = useSearchParams();
  const paginationQueryParamPrefixToUse = paginationQueryParamPrefix
    ? `${paginationQueryParamPrefix}_`
    : '';

  const updateRows = (args: any) => {
    const newPage = args.page;
    const { pageSize } = args;

    searchParams.set(`${paginationQueryParamPrefixToUse}page`, newPage);
    searchParams.set(`${paginationQueryParamPrefixToUse}per_page`, pageSize);
    setSearchParams(searchParams);
  };

  if (pagination) {
    const maxPages = 1000;
    const pagesUnknown = pagination.pages > maxPages;
    const totalItems =
      pagination.pages < maxPages ? pagination.total : maxPages * perPage;
    const itemText = () => {
      const start = (page - 1) * perPage + 1;
      return `Items ${start} to ${start + pagination.count} of ${
        pagination.total
      }`;
    };

    return (
      <>
        {tableToDisplay}
        <Pagination
          className={paginationClassName}
          data-qa={paginationDataQATag}
          backwardText="Previous page"
          forwardText="Next page"
          itemsPerPageText="Items per page:"
          page={page}
          pageNumberText="Page Number"
          itemText={itemText}
          pageSize={perPage}
          pageSizes={perPageOptions || PER_PAGE_OPTIONS}
          totalItems={totalItems}
          onChange={updateRows}
          pagesUnknown={pagesUnknown}
        />
      </>
    );
  }
  return null;
}
