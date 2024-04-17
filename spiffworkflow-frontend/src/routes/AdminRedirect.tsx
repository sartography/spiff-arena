import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function AdminRedirect() {
  const navigate = useNavigate();
  useEffect(() => {
    let newPath = window.location.pathname.replace(/^\/admin\//, '/');
    const queryParams = window.location.search;
    newPath = `${newPath}${queryParams}`;
    navigate(newPath);
  }, [navigate]);

  return null;
}
