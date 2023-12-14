import React, { useEffect, useState } from 'react';
// @ts-ignore
// @ts-ignore
import { Table, Button } from '@carbon/react';
import { useSearchParams } from 'react-router-dom';
import PaginationForTable from '../PaginationForTable';
import ProcessBreadcrumb from '../ProcessBreadcrumb';
import { getPageInfoFromSearchParams } from '../../helpers';
import HttpService from '../../services/HttpService';
import { ReferenceCache } from '../../interfaces';
import MessageModal from './MessageModal';

type OwnProps = {
  processGroupId?: string;
};

export default function MessageModelList({ processGroupId }: OwnProps) {
  const [messageModels, setMessageModels] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [searchParams] = useSearchParams();

  const [messageModelForModal, setMessageModelForModal] =
    useState<ReferenceCache | null>(null);

  useEffect(() => {
    const setMessageInstanceListFromResult = (result: any) => {
      setMessageModels(result.results);
      setPagination(result.pagination);
    };
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    let queryParamString = `per_page=${perPage}&page=${page}`;
    if (processGroupId) {
      queryParamString += `&relative_location=${processGroupId}`;
    }

    HttpService.makeCallToBackend({
      path: `/message-models?${queryParamString}`,
      successCallback: setMessageInstanceListFromResult,
    });
  }, [processGroupId, searchParams]);

  const handleMessageEditClose = () => {
    setMessageModelForModal(null);
  };

  const messageEditModal = () => {
    console.log('Message Model for Modal', messageModelForModal);
    if (messageModelForModal) {
      return (
        <MessageModal
          messageModel={messageModelForModal}
          open={!!messageModelForModal}
          onClose={handleMessageEditClose}
        />
      );
    }
    return null;
  };

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
          <td>{row.relative_location}</td>
          <td>{correlation(row)}</td>
          <td>
            <Button
              className="button-link"
              kind="secondary"
              style={{ width: '60px' }}
              size="sm"
              onClick={() => setMessageModelForModal(row)}
            >
              Edit
            </Button>
          </td>
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
            <th>Edit</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </Table>
    );
  };
  if (pagination) {
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    let breadcrumbElement = null;
    if (searchParams.get('process_instance_id')) {
      breadcrumbElement = (
        <ProcessBreadcrumb
          hotCrumbs={[
            ['Process Groups', '/process-groups'],
            {
              entityToExplode: searchParams.get('process_model_id') || '',
              entityType: 'process-model-id',
              linkLastItem: true,
            },
            [
              `Process Instance: ${searchParams.get('process_instance_id')}`,
              `/process-instances/${searchParams.get(
                'process_model_id'
              )}/${searchParams.get('process_instance_id')}`,
            ],
            ['Messages'],
          ]}
        />
      );
    }
    return (
      <>
        {messageEditModal()}
        {breadcrumbElement}
        <PaginationForTable
          page={page}
          perPage={perPage}
          pagination={pagination}
          tableToDisplay={buildTable()}
          paginationQueryParamPrefix="message-list"
        />
      </>
    );
  }
  return null;
}
