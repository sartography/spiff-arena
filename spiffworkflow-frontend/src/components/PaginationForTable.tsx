import { useSearchParams } from 'react-router-dom';
import { TablePagination } from '@mui/material';
import { ChangeEvent, MouseEvent } from 'react';
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

  const updateRows = (
    event: MouseEvent<HTMLButtonElement> | null,
    newPage: number,
  ) => {
    searchParams.set(
      `${paginationQueryParamPrefixToUse}page`,
      String(newPage + 1),
    );
    setSearchParams(searchParams);
  };

  const handleChangeRowsPerPage = (event: ChangeEvent<HTMLInputElement>) => {
    const newPerPage = parseInt(event.target.value, 10);
    searchParams.set(
      `${paginationQueryParamPrefixToUse}per_page`,
      String(newPerPage),
    );
    setSearchParams(searchParams);
  };

  if (pagination) {
    const maxPages = 1000;
    const totalItems =
      pagination.pages < maxPages ? pagination.total : maxPages * perPage;

    return (
      <>
        {tableToDisplay}
        <TablePagination
          className={paginationClassName}
          data-qa={paginationDataQATag}
          component="div"
          count={totalItems}
          page={page - 1}
          onPageChange={updateRows}
          rowsPerPage={perPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          rowsPerPageOptions={perPageOptions || PER_PAGE_OPTIONS}
          labelRowsPerPage="Items per page:"
          labelDisplayedRows={({ from, to, count }) =>
            `${from}-${to} of ${count}`
          }
        />
      </>
    );
  }
  return null;
}
