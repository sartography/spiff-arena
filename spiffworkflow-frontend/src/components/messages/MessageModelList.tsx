import React, { useEffect, useState } from 'react';
import { Table } from '@carbon/react';
import { useSearchParams } from 'react-router-dom';
import PaginationForTable from '../PaginationForTable';
import {
  getPageInfoFromSearchParams,
  modifyProcessIdentifierForPathParam,
} from '../../helpers';
import HttpService from '../../services/HttpService';
import { PaginationObject, ReferenceCache } from '../../interfaces';

// TODO: update to work with current message-models api
type OwnProps = {
  processGroupId?: string;
};

export default function MessageModelList({ processGroupId }: OwnProps) {
  const [messageModels, setMessageModels] = useState<ReferenceCache[]>([]);
  const [pagination, setPagination] = useState<PaginationObject | null>(null);
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const setMessageInstanceListFromResult = (result: any) => {
      setMessageModels(result.results);
      setPagination(result.pagination);
    };
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    const queryParamString = `per_page=${perPage}&page=${page}`;
    let modifiedProcessIdentifierForPathParam = '';
    if (processGroupId) {
      modifiedProcessIdentifierForPathParam = `/${modifyProcessIdentifierForPathParam(
        processGroupId,
      )}`;
    }

    HttpService.makeCallToBackend({
      path: `/message-models${modifiedProcessIdentifierForPathParam}?${queryParamString}`,
      successCallback: setMessageInstanceListFromResult,
    });
  }, [processGroupId, searchParams]);

  const correlation = (row: ReferenceCache): string => {
    let keys = '';
    const cProps: string[] = [];
    if ('correlation_keys' in row.properties) {
      keys = row.properties.correlation_keys;
    }
    if ('correlations' in row.properties) {
      row.properties.correlations.forEach((cor: any) => {
        cProps.push(cor.correlation_property);
      });
    }
    if (cProps.length > 0) {
      keys += ` (${cProps.join(', ')})`;
    }
    return keys;
  };

  const buildTable = () => {
    const rows = messageModels.map((row: ReferenceCache) => {
      return (
        <tr key={row.identifier}>
          <td>{row.identifier}</td>
          <td>
            <a
              href={`/process-groups/${modifyProcessIdentifierForPathParam(
                row.relative_location,
              )}`}
            >
              {row.relative_location}
            </a>
          </td>
          <td>{correlation(row)}</td>
        </tr>
      );
    });
    return (
      <Table striped bordered>
        <thead>
          <tr>
            <th>Id</th>
            <th>Location</th>
            <th>Correlation</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </Table>
    );
  };
  if (pagination) {
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    return (
      <PaginationForTable
        page={page}
        perPage={perPage}
        pagination={pagination}
        tableToDisplay={buildTable()}
        paginationQueryParamPrefix="message-model-list"
      />
    );
  }
  return null;
}
