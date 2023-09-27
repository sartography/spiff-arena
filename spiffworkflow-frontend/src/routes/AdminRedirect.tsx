import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function AdminRedirect() {
  const navigate = useNavigate();
  useEffect(() => {
    const newPath = window.location.pathname.replace('/admin/', '/');
    navigate(newPath);
  }, [navigate]);

  return null;
}
