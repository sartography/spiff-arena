import {Tab, TabList, TabPanel, TabPanels, Tabs} from '@carbon/react';
import { useNavigate } from 'react-router-dom';
import MessageInstanceList from '../components/messages/MessageInstanceList';
import { setPageTitle } from '../helpers';
import MessageModelList from "../components/messages/MessageModelList";

export default function MessageListPage() {
  const navigate = useNavigate();
  setPageTitle(['Messages']);

  return (
    <>
      <h1>Messages</h1>
      <Tabs>
        <TabList aria-label="List of tabs">
          <Tab>Message Instances</Tab>
          <Tab>Message Models</Tab>
        </TabList>
        <TabPanels>
          <TabPanel>
            <MessageInstanceList />
          </TabPanel>
          <TabPanel>
            <MessageModelList />
          </TabPanel>
        </TabPanels>
      </Tabs>

    </>
  );
}
