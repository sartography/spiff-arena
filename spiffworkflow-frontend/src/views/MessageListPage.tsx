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
    searchParams.get('tab') === 'models' ? 'models' : 'instances';
  const initialMessageId = searchParams.get('message_id') || undefined;
  const initialSourceLocation =
    searchParams.get('source_location') || undefined;

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
          const nextSearchParams = new URLSearchParams();
          nextSearchParams.set('tab', nextTab);
          setSearchParams(nextSearchParams);
        }}
        aria-label="Messages tabs"
        sx={{ mb: 2 }}
      >
        <Tab value="instances" label={t('message_instances_tab')} />
        <Tab value="models" label={t('message_models_tab')} />
      </Tabs>
      {selectedTab === 'models' ? (
        <MessageModelList
          initialMessageId={initialMessageId}
          initialSourceLocation={initialSourceLocation}
        />
      ) : (
        <MessageInstanceList />
      )}
    </Box>
  );
}
