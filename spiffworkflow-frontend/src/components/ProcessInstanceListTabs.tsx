// @ts-ignore
import { Tabs, Tab } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { Can } from '@casl/react';
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

  let selectedTabIndex = 0;
  if (variant === 'all') {
    selectedTabIndex = 1;
  } else if (variant === 'find-by-id') {
    selectedTabIndex = 2;
  }

  return (
    <Tabs value={selectedTabIndex} aria-label={t('list_of_tabs')}>
      <SpiffTooltip title={t('tooltip_only_show_for_me')}>
        <Tab
          label={t('for_me')}
          data-testid="process-instance-list-for-me"
          onClick={() => {
            navigate('/process-instances/for-me');
          }}
        />
      </SpiffTooltip>
      <Can I="GET" a={targetUris.processInstanceListPath} ability={ability}>
        <SpiffTooltip title={t('tooltip_show_for_all')}>
          <Tab
            label={t('all')}
            data-testid="process-instance-list-all"
            onClick={() => {
              navigate('/process-instances/all');
            }}
          />
        </SpiffTooltip>
      </Can>
      <SpiffTooltip title={t('tooltip_search_by_id')}>
        <Tab
          label={t('find_by_id')}
          data-testid="process-instance-list-find-by-id"
          onClick={() => {
            navigate('/process-instances/find-by-id');
          }}
        />
      </SpiffTooltip>
    </Tabs>
  );
}
