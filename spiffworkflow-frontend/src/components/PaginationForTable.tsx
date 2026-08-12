import { useSearchParams } from 'react-router-dom';
import {
  FormControl,
  InputLabel,
  Select,
  Stack,
  TablePagination,
} from '@mui/material';
import { ChangeEvent, MouseEvent, useId } from 'react';
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

  const setPageSearchParam = (newPage: number) => {
    searchParams.set(`${paginationQueryParamPrefixToUse}page`, String(newPage));
    setSearchParams(searchParams);
  };

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
    const totalPages = Math.min(pagination.pages, MAX_PAGES);
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
              t('pagination_display', { from, to, count })
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
