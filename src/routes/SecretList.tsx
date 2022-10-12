import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Button, Table } from 'react-bootstrap';
import PaginationForTable from '../components/PaginationForTable';
import HttpService from '../services/HttpService';
import { getPageInfoFromSearchParams } from '../helpers';

export default function SecretList() {
  const [searchParams] = useSearchParams();

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

  const buildTable = () => {
    const rows = secrets.map((row) => {
      return (
        <tr key={(row as any).key}>
          <td>
            <Link to={`/admin/secrets/${(row as any).key}`}>
              {(row as any).key}
            </Link>
          </td>
          <td>{(row as any).value}</td>
          <td>{(row as any).username}</td>
        </tr>
      );
    });
    return (
      <Table striped bordered>
        <thead>
          <tr>
            <th>Secret Key</th>
            <th>Secret Value</th>
            <th>Creator</th>
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
          path="/admin/secrets"
        />
      );
    } else {
      displayText = <p>No Secrets to Display</p>;
    }
    return displayText;
  };

  if (pagination) {
    return (
      <>
        <Button href="/admin/secrets/new">Add a secret</Button>
        <br />
        <br />
        {SecretsDisplayArea()}
      </>
    );
  }
  return null;
}
