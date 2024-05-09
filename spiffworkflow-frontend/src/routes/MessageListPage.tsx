import MessageInstanceList from '../components/messages/MessageInstanceList';
import { setPageTitle } from '../helpers';

export default function MessageListPage() {
  setPageTitle(['Messages']);

  // TODO: add tabs back in when MessageModelList is working again
  // TODO: only load the component for the tab we are currently on
  // return (
  //   <>
  //     <h1>Messages</h1>
  //     <Tabs>
  //       <TabList aria-label="List of tabs">
  //         <Tab>Message Instances</Tab>
  //         <Tab>Message Models</Tab>
  //       </TabList>
  //       <TabPanels>
  //         <TabPanel>
  //           <MessageInstanceList />
  //         </TabPanel>
  //         <TabPanel>
  //           <MessageModelList />
  //         </TabPanel>
  //       </TabPanels>
  //     </Tabs>
  //   </>
  // );

  return (
    <>
      <h1>Messages</h1>
      <MessageInstanceList />
    </>
  );
}
