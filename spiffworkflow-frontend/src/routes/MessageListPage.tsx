import MessageInstanceList from '../components/MessageInstanceList';
import { setPageTitle } from '../helpers';

export default function MessageListPage() {
  setPageTitle(['Messages']);
  return (
    <>
      <h1>Messages</h1>
      <MessageInstanceList />
    </>
  );
}
