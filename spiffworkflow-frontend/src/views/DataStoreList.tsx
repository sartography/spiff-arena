import React from 'react';
import { Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';
import DataStoreListTable from '../components/DataStoreListTable';
import { setPageTitle } from '../helpers';

export default function DataStoreList() {
  const { t } = useTranslation();
  setPageTitle([t('data_stores')]);
  return (
    <>
      <Typography variant="h1" sx={{ mb: 2 }}>
        {t('data_stores')}
      </Typography>
      <DataStoreListTable />
    </>
  );
}
