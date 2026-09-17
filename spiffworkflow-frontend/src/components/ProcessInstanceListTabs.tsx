// @ts-ignore
import { Tabs, Tab } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Can } from '../contexts/Can';
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

  return (
    <Can
      I="GET"
      a={targetUris.processInstanceListPath}
      ability={ability}
      passThrough
    >
      {(canViewAll) => {
        let selectedTabValue: string | false = 'for_me';
        if (variant === 'all') {
          selectedTabValue = canViewAll ? 'all' : false;
        } else if (variant === 'find-by-id') {
          selectedTabValue = 'find_by_id';
        }

        return (
          <Tabs value={selectedTabValue} aria-label={t('list_of_tabs')}>
            {canViewAll && (
              <Tab
                label={
                  <SpiffTooltip title={t('tooltip_show_for_all')}>
                    <span>{t('all')}</span>
                  </SpiffTooltip>
                }
                value="all"
                data-testid="process-instance-list-all"
                onClick={() => {
                  navigate('/process-instances/all');
                }}
              />
            )}
            <Tab
              label={
                <SpiffTooltip title={t('tooltip_only_show_for_me')}>
                  <span>{t('for_me')}</span>
                </SpiffTooltip>
              }
              value="for_me"
              data-testid="process-instance-list-for-me"
              onClick={() => {
                navigate('/process-instances/for-me');
              }}
            />
            <Tab
              label={
                <SpiffTooltip title={t('tooltip_search_by_id')}>
                  <span>{t('find_by_id')}</span>
                </SpiffTooltip>
              }
              value="find_by_id"
              data-testid="process-instance-list-find-by-id"
              onClick={() => {
                navigate('/process-instances/find-by-id');
              }}
            />
          </Tabs>
        );
      }}
    </Can>
  );
}
