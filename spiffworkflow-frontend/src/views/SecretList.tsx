import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import {
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
} from '@mui/material';
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
        <TableRow key={(row as any).key}>
          <TableCell>
            <Link to={`/configuration/secrets/${(row as any).key}`}>
              {(row as any).id}
            </Link>
          </TableCell>
          <TableCell>
            <Link to={`/configuration/secrets/${(row as any).key}`}>
              {(row as any).key}
            </Link>
          </TableCell>
          <TableCell>{(row as any).username}</TableCell>
          <TableCell aria-label="Delete">
            <MdDelete onClick={() => handleDeleteSecret((row as any).key)} />
          </TableCell>
        </TableRow>
      );
    });
    return (
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Id</TableCell>
              <TableCell>Secret Key</TableCell>
              <TableCell>Creator</TableCell>
              <TableCell>Delete</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>{rows}</TableBody>
        </Table>
      </TableContainer>
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
        <Typography variant="h1">Secrets</Typography>
        {SecretsDisplayArea()}
        <Button
          component={Link}
          variant="contained"
          to="/configuration/secrets/new"
        >
          Add a secret
        </Button>
      </div>
    );
  }
  return null;
}
