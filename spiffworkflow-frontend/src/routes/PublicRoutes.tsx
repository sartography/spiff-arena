import { Content } from '@carbon/react';
import { Route, Routes } from 'react-router-dom';
import PublicForm from './public/PublicForm';
import SignOut from './public/SignOut';

export default function PublicRoutes() {
  return (
    <Content className="main-site-body-centered">
      <Routes>
        <Route
          path="/tasks/:process_instance_id/:task_guid"
          element={<PublicForm />}
        />
        <Route path="/:modified_message_name" element={<PublicForm />} />
        <Route path="/sign-out" element={<SignOut />} />
      </Routes>
    </Content>
  );
}
