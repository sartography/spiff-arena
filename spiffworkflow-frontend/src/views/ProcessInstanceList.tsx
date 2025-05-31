import React from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Box } from '@mui/material'; // MUI components

import 'react-datepicker/dist/react-datepicker.css';

import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import ProcessInstanceListTableWithFilters from '../components/ProcessInstanceListTableWithFilters';
import {
  getProcessModelFullIdentifierFromSearchParams,
  setPageTitle,
} from '../helpers';
import ProcessInstanceListTabs from '../components/ProcessInstanceListTabs';

type OwnProps = {
  variant: string;
};

export default function ProcessInstanceList({ variant }: OwnProps) {
  const [searchParams] = useSearchParams();
  const { t } = useTranslation();
  setPageTitle([t('process_instances')]);

  const processInstanceBreadcrumbElement = () => {
    const processModelFullIdentifier =
      getProcessModelFullIdentifierFromSearchParams(searchParams);
    if (processModelFullIdentifier === null) {
      return null;
    }

    return (
      <ProcessBreadcrumb
        hotCrumbs={[
          [t('process_groups'), '/process-groups'],
          {
            entityToExplode: processModelFullIdentifier,
            entityType: 'process-model-id',
            linkLastItem: true,
          },
          [t('process_instances')],
        ]}
      />
    );
  };

  const processInstanceTitleElement = () => {
    let headerText = t('my_process_instances');
    if (variant === 'all') {
      headerText = t('all_process_instances');
    }
    return { text: headerText };
  };

  return (
    <Box>
      <ProcessInstanceListTabs variant={variant} />
      <br />
      {processInstanceBreadcrumbElement()}
      <ProcessInstanceListTableWithFilters
        variant={variant}
        showActionsColumn
        header={processInstanceTitleElement()}
      />
    </Box>
  );
}
