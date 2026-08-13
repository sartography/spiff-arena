import { useSearchParams } from 'react-router-dom';
import { TablePagination } from '@mui/material';
import { ChangeEvent, MouseEvent, useCallback, useEffect } from 'react';
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

  const setPageSearchParam = useCallback(
    (newPage: number) => {
      searchParams.set(
        `${paginationQueryParamPrefixToUse}page`,
        String(newPage),
      );
      setSearchParams(searchParams);
    },
    [searchParams, setSearchParams, paginationQueryParamPrefixToUse],
  );

  // a page beyond the data, e.g. from a hand-edited or stale url, snaps back
  // to the last page that actually exists.
  const lastPage = pagination ? Math.max(pagination.pages, 1) : null;
  useEffect(() => {
    if (lastPage !== null && page > lastPage) {
      setPageSearchParam(lastPage);
    }
  }, [lastPage, page, setPageSearchParam]);

  const updateRows = (
    _event: MouseEvent<HTMLButtonElement> | null,
    newPage: number,
  ) => {
    setPageSearchParam(newPage + 1);
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
    return (
      <>
        {tableToDisplay}
        <TablePagination
          className={paginationClassName}
          data-testid={paginationDataTestidTag}
          component="div"
          count={pagination.total}
          page={page - 1}
          onPageChange={updateRows}
          rowsPerPage={perPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          rowsPerPageOptions={perPageOptions || PER_PAGE_OPTIONS}
          showFirstButton
          showLastButton
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
