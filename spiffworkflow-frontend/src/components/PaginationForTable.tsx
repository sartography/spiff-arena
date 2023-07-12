import { useSearchParams } from 'react-router-dom';

// @ts-ignore
import { Pagination } from '@carbon/react';
import { PaginationObject } from '../interfaces';

export const DEFAULT_PER_PAGE = 50;
export const DEFAULT_PAGE = 1;

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
          pageSize={perPage}
          pageSizes={perPageOptions || PER_PAGE_OPTIONS}
          totalItems={pagination.total}
          onChange={updateRows}
        />
      </>
    );
  }
  return null;
}
