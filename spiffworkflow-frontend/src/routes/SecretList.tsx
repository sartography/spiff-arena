import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
// @ts-ignore
import { Button, Table, DatePicker, DatePickerInput } from '@carbon/react';
import { MdDelete } from 'react-icons/md';
import PaginationForTable from '../components/PaginationForTable';
import HttpService from '../services/HttpService';
import { getPageInfoFromSearchParams } from '../helpers';

export default function SecretList() {
  const [searchParams] = useSearchParams();

  const [dateRange, setDateRange] = useState([]);

  const [secrets, setSecrets] = useState([]);
  const [pagination, setPagination] = useState(null);

  useEffect(() => {
    const setSecretsFromResult = (result: any) => {
      setSecrets(result.results);
      setPagination(result.pagination);
    };
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    HttpService.makeCallToBackend({
      path: `/secrets?per_page=${perPage}&page=${page}`,
      successCallback: setSecretsFromResult,
    });
  }, [searchParams]);

  const reloadSecrets = (_result: any) => {
    window.location.reload();
  };

  const handleDeleteSecret = (key: any) => {
    HttpService.makeCallToBackend({
      path: `/secrets/${key}`,
      successCallback: reloadSecrets,
      httpMethod: 'DELETE',
    });
  };

  const buildTable = () => {
    const rows = secrets.map((row) => {
      return (
        <tr key={(row as any).key}>
          <td>
            <Link to={`/admin/configuration/secrets/${(row as any).key}`}>
              {(row as any).id}
            </Link>
          </td>
          <td>
            <Link to={`/admin/configuration/secrets/${(row as any).key}`}>
              {(row as any).key}
            </Link>
          </td>
          <td>{(row as any).username}</td>
          <td>
            <MdDelete onClick={() => handleDeleteSecret((row as any).key)} />
          </td>
        </tr>
      );
    });
    return (
      <Table striped bordered>
        <thead>
          <tr>
            <th>Id</th>
            <th>Secret Key</th>
            <th>Creator</th>
            <th>Delete</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </Table>
    );
  };

  const SecretsDisplayArea = () => {
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    let displayText = null;
    if (secrets?.length > 0) {
      displayText = (
        <PaginationForTable
          page={page}
          perPage={perPage}
          pagination={pagination as any}
          tableToDisplay={buildTable()}
        />
      );
    } else {
      displayText = <p>No Secrets to Display</p>;
    }
    return displayText;
  };

  if (pagination) {
    return (
      <div>
        <h1>Secrets</h1>
        <DatePicker
          onChange={(selectedDates: any) => {
            setDateRange(selectedDates);
          }}
          value={dateRange}
          dateFormat="Y-m-d"
          datePickerType="range"
        >
          <DatePickerInput
            id="from"
            placeholder="yyyy-mm-dd"
            labelText="from"
          />
          <DatePickerInput id="to" placeholder="yyyy-mm-dd" labelText="to" />
        </DatePicker>
        {SecretsDisplayArea()}
        <Button href="/admin/configuration/secrets/new">Add a secret</Button>
      </div>
    );
  }
  return null;
}
