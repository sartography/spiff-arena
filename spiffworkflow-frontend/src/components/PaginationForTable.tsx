import { useSearchParams } from 'react-router-dom';
import {
  FormControl,
  InputLabel,
  Select,
  Stack,
  TablePagination,
} from '@mui/material';
import { ChangeEvent, MouseEvent, useCallback, useEffect, useId } from 'react';
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
  const MAX_PAGES = 1000;
  const [searchParams, setSearchParams] = useSearchParams();
  const goToPageSelectId = useId();
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

  // the ui does not paginate past MAX_PAGES, so a page beyond that (or beyond
  // the data, e.g. from a hand-edited url) snaps back to the last valid page.
  const totalPages = pagination ? Math.min(pagination.pages, MAX_PAGES) : null;
  useEffect(() => {
    if (totalPages !== null && page > totalPages) {
      setPageSearchParam(Math.max(totalPages, 1));
    }
  }, [totalPages, page, setPageSearchParam]);

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

  if (pagination && totalPages !== null) {
    // when the data has more pages than the ui will paginate through, the
    // displayed count is capped and the label says "more than" to be honest
    // about the fact that more results exist.
    const isCapped = pagination.pages > MAX_PAGES;
    const totalItems =
      pagination.pages < MAX_PAGES ? pagination.total : MAX_PAGES * perPage;

    // native select options stay fast even with the MAX_PAGES worst case.
    // each option shows the page number and the item range it covers, so the
    // meaning of a page is clear regardless of the per-page setting.
    const pageOptions = [];
    for (let pageOption = 1; pageOption <= totalPages; pageOption += 1) {
      const from = (pageOption - 1) * perPage + 1;
      const to = Math.min(pageOption * perPage, totalItems);
      pageOptions.push(
        <option key={pageOption} value={pageOption}>
          {`${pageOption} (${from}-${to})`}
        </option>,
      );
    }

    return (
      <>
        {tableToDisplay}
        <Stack
          direction="row"
          spacing={1}
          sx={{ alignItems: 'center', justifyContent: 'flex-end' }}
        >
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
            showFirstButton
            showLastButton
            labelRowsPerPage={t('pagination_items_per_page')}
            labelDisplayedRows={({ from, to, count }) =>
              t(
                isCapped
                  ? 'pagination_display_more_than'
                  : 'pagination_display',
                { from, to, count },
              )
            }
          />
          <FormControl size="small" variant="standard">
            <InputLabel htmlFor={goToPageSelectId}>
              {t('pagination_go_to_page')}
            </InputLabel>
            <Select
              native
              value={page}
              data-testid="pagination-page-select"
              inputProps={{ id: goToPageSelectId }}
              onChange={(event) => {
                const newPage = Number(event.target.value);
                if (newPage !== page) {
                  setPageSearchParam(newPage);
                }
              }}
            >
              {pageOptions}
            </Select>
          </FormControl>
        </Stack>
      </>
    );
  }
  return null;
}
