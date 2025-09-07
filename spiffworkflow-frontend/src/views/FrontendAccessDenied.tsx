import { Typography, Box, Paper } from '@mui/material';
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { setPageTitle } from '../helpers';

export default function FrontendAccessDenied() {
  const { t } = useTranslation();
  
  useEffect(() => {
    setPageTitle([t('frontend_access_denied_title')]);
  }, [t]);
  
  return (
    <Box sx={{ mt: 2, mb: 4, mx: 2 }}>
      <Typography variant="h1" sx={{ mb: 2 }}>
        {t('frontend_access_denied_title')}
      </Typography>
      <Paper elevation={2} sx={{ p: 3, maxWidth: '800px' }}>
        <Typography variant="body1">
          {t('frontend_access_denied_message')}
        </Typography>
      </Paper>
    </Box>
  );
}