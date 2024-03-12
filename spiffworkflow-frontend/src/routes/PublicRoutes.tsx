import { Content } from '@carbon/react';
import { Route, Routes } from 'react-router-dom';
import MessageStartEventForm from './public/MessageStartEventForm';

export default function PublicRoutes() {
  return (
    <Content className="main-site-body-centered">
      <Routes>
        <Route
          path="/:modified_message_name"
          element={<MessageStartEventForm />}
        />
      </Routes>
    </Content>
  );
}
