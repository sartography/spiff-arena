import { useEffect, useState } from 'react';
import Nav from 'react-bootstrap/Nav';
import { useLocation } from 'react-router-dom';

export default function SubNavigation() {
  const location = useLocation();
  const [activeKey, setActiveKey] = useState('');

  useEffect(() => {
    let newActiveKey = '/admin/process-groups';
    if (location.pathname.match(/^\/admin\/messages\b/)) {
      newActiveKey = '/admin/messages';
    } else if (location.pathname.match(/^\/admin\/process-instances\b/)) {
      newActiveKey = '/admin/process-instances';
    } else if (location.pathname.match(/^\/admin\/secrets\b/)) {
      newActiveKey = '/admin/secrets';
    } else if (location.pathname === '/') {
      newActiveKey = '/';
    } else if (location.pathname.match(/^\/tasks\b/)) {
      newActiveKey = '/';
    }
    setActiveKey(newActiveKey);
  }, [location]);

  if (activeKey) {
    return (
      <Nav variant="tabs" activeKey={activeKey}>
        <Nav.Item data-qa="nav-home">
          <Nav.Link href="/">Home</Nav.Link>
        </Nav.Item>
        <Nav.Item>
          <Nav.Link href="/admin/process-groups">Process Models</Nav.Link>
        </Nav.Item>
        <Nav.Item>
          <Nav.Link href="/admin/process-instances">Process Instances</Nav.Link>
        </Nav.Item>
        <Nav.Item>
          <Nav.Link href="/admin/messages">Messages</Nav.Link>
        </Nav.Item>
        <Nav.Item>
          <Nav.Link href="/admin/secrets">Secrets</Nav.Link>
        </Nav.Item>
      </Nav>
    );
  }
  return null;
}
