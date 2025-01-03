import React from 'react';
import { Typography, Tabs, Tab, Box } from '@mui/material';
import MessageInstanceList from '../components/messages/MessageInstanceList';
import { setPageTitle } from '../../helpers';

export default function MessageListPage() {
  setPageTitle(['Messages']);

  const [value, setValue] = React.useState(0);

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  return (
    <>
      <Typography variant="h4" component="h1" gutterBottom>
        Messages
      </Typography>
      <Tabs value={value} onChange={handleChange} aria-label="Message tabs">
        <Tab label="Message Instances" />
        <Tab label="Message Models" />
      </Tabs>
      <Box role="tabpanel" hidden={value !== 0}>
        <MessageInstanceList />
      </Box>
      <Box role="tabpanel" hidden={value !== 1}>
        {/* Placeholder for MessageModelList */}
        <Typography variant="body1">Message Models content goes here.</Typography>
      </Box>
    </>
  );
}
