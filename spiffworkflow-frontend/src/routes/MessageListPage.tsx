import MessageInstanceList from '../components/MessageInstanceList';
import { setPageTitle } from '../helpers';

export default function MessageListPage() {
  setPageTitle(['Mensagens']);
  return (
    <>
      <h1>Mensagens</h1>
      <MessageInstanceList />
    </>
  );
}
