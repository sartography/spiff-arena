import { useSearchParams } from 'react-router-dom';
import { TablePagination } from '@mui/material';
import { ChangeEvent, MouseEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { PaginationObject } from '../interfaces';

type OwnProps = {
  page: number;
  perPage: number;
  perPageOptions?: number[];
  pagination: PaginationObject | null;
  tableToDisplay: any;
  paginationQueryParamPrefix?: string;
  paginationClassName?: string;
  paginationDataTestidTag?: string;
};

export default function PaginationForTable({
  page,
  perPage,
  perPageOptions,
  pagination,
  tableToDisplay,
  paginationQueryParamPrefix,
  paginationClassName,
  paginationDataTestidTag = 'pagination-options',
}: OwnProps) {
  const { t } = useTranslation();
  const PER_PAGE_OPTIONS = [2, 10, 50, 100];
  const [searchParams, setSearchParams] = useSearchParams();
  const paginationQueryParamPrefixToUse = paginationQueryParamPrefix
    ? `${paginationQueryParamPrefix}_`
    : '';

  const updateRows = (
    _event: MouseEvent<HTMLButtonElement> | null,
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
          data-testid={paginationDataTestidTag}
          component="div"
          count={totalItems}
          page={page - 1}
          onPageChange={updateRows}
          rowsPerPage={perPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          rowsPerPageOptions={perPageOptions || PER_PAGE_OPTIONS}
          labelRowsPerPage={t('pagination_items_per_page')}
          labelDisplayedRows={({ from, to, count }) =>
            t('pagination_display', { from, to, count })
          }
        />
      </>
    );
  }
  return null;
}
