// @ts-ignore
import { Tabs, Tab } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { Can } from '../contexts/Can';
import { useNavigate } from 'react-router-dom';
import { usePermissionFetcher } from '../hooks/PermissionService';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { PermissionsToCheck } from '../interfaces';
import SpiffTooltip from './SpiffTooltip';

type OwnProps = {
  variant: string;
};

export default function ProcessInstanceListTabs({ variant }: OwnProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.processInstanceListPath]: ['GET'],
  };
  const { ability } = usePermissionFetcher(permissionRequestData);

  let selectedTabIndex = 'for_me';
  if (variant === 'all') {
    selectedTabIndex = 'for_me';
  } else if (variant === 'find-by-id') {
    selectedTabIndex = 'find_by_id';
  }

  return (
    <Tabs value="for_me" aria-label={t('list_of_tabs')}>
      <Can I="GET" a={targetUris.processInstanceListPath} ability={ability}>
        <SpiffTooltip title={t('tooltip_show_for_all')}>
          <Tab
            label={t('all')}
            value="all"
            data-testid="process-instance-list-all"
            onClick={() => {
              navigate('/process-instances/all');
            }}
          />
        </SpiffTooltip>
      </Can>
      <SpiffTooltip title={t('tooltip_only_show_for_me')}>
        <Tab
          label={t('for_me')}
          value="for_me"
          data-testid="process-instance-list-for-me"
          onClick={() => {
            navigate('/process-instances/for-me');
          }}
        />
      </SpiffTooltip>
      <SpiffTooltip title={t('tooltip_search_by_id')}>
        <Tab
          label={t('find_by_id')}
          value="find_by_id"
          data-testid="process-instance-list-find-by-id"
          onClick={() => {
            navigate('/process-instances/find-by-id');
          }}
        />
      </SpiffTooltip>
    </Tabs>
  );
}
