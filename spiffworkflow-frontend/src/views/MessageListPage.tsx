import { Typography, Box, Tab, Tabs } from '@mui/material';
import React, { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import MessageInstanceList from '../components/messages/MessageInstanceList';
import MessageModelList from '../components/messages/MessageModelList';
import { setPageTitle } from '../helpers';
import { useSearchParams } from 'react-router-dom';

export default function MessageListPage() {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedTab =
    searchParams.get('tab') === 'instances' ? 'instances' : 'models';

  useEffect(() => {
    setPageTitle([t('messages')]);
  }, [t]);

  return (
    <Box>
      <Typography variant="h1" sx={{ mb: 2 }}>
        {t('messages')}
      </Typography>
      <Tabs
        value={selectedTab}
        onChange={(_event, nextTab) => {
          const nextSearchParams = new URLSearchParams(searchParams);
          nextSearchParams.set('tab', nextTab);
          setSearchParams(nextSearchParams);
        }}
        aria-label="Messages tabs"
        sx={{ mb: 2 }}
      >
        <Tab value="models" label="Message Models" />
        <Tab value="instances" label="Message Instances" />
      </Tabs>
      {selectedTab === 'models' ? (
        <MessageModelList />
      ) : (
        <MessageInstanceList />
      )}
    </Box>
  );
}
