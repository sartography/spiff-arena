import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
// @ts-ignore
import { Button, Table } from '@carbon/react';
import { MdDelete } from 'react-icons/md';
import PaginationForTable from '../components/PaginationForTable';
import HttpService from '../services/HttpService';
import { getPageInfoFromSearchParams } from '../helpers';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { PermissionsToCheck } from '../interfaces';
import { usePermissionFetcher } from '../hooks/PermissionService';

export default function SecretList() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [secrets, setSecrets] = useState([]);
  const [pagination, setPagination] = useState(null);

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.authenticationListPath]: ['GET'],
    [targetUris.secretListPath]: ['GET'],
  };
  const { ability, permissionsLoaded } = usePermissionFetcher(
    permissionRequestData,
  );

  useEffect(() => {
    const setSecretsFromResult = (result: any) => {
      setSecrets(result.results);
      setPagination(result.pagination);
    };
    if (permissionsLoaded) {
      if (
        !ability.can('GET', targetUris.secretListPath) &&
        ability.can('GET', targetUris.authenticationListPath)
      ) {
        navigate('/configuration/authentications');
      } else {
        const { page, perPage } = getPageInfoFromSearchParams(searchParams);
        HttpService.makeCallToBackend({
          path: `/secrets?per_page=${perPage}&page=${page}`,
          successCallback: setSecretsFromResult,
        });
      }
    }
  }, [
    searchParams,
    permissionsLoaded,
    ability,
    navigate,
    targetUris.authenticationListPath,
    targetUris.secretListPath,
  ]);

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
            <Link to={`/configuration/secrets/${(row as any).key}`}>
              {(row as any).id}
            </Link>
          </td>
          <td>
            <Link to={`/configuration/secrets/${(row as any).key}`}>
              {(row as any).key}
            </Link>
          </td>
          <td>{(row as any).username}</td>
          <td aria-label="Delete">
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
        {SecretsDisplayArea()}
        <Button href="/configuration/secrets/new">Add a secret</Button>
      </div>
    );
  }
  return null;
}
