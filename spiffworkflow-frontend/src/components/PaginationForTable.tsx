import { useNavigate } from 'react-router-dom';

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
  queryParamString?: string;
  path: string;
};

export default function PaginationForTable({
  page,
  perPage,
  perPageOptions,
  pagination,
  tableToDisplay,
  queryParamString = '',
  path,
}: OwnProps) {
  const PER_PAGE_OPTIONS = [2, 10, 50, 100];
  const navigate = useNavigate();

  const updateRows = (args: any) => {
    const newPage = args.page;
    const { pageSize } = args;
    navigate(`${path}?page=${newPage}&per_page=${pageSize}${queryParamString}`);
  };

  if (pagination) {
    return (
      <>
        {tableToDisplay}
        <Pagination
          data-qa="pagination-options"
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
