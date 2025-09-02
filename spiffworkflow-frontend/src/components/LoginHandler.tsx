import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import UserService from '../services/UserService';

export default function LoginHandler() {
  const navigate = useNavigate();

  useEffect(() => {
    // Check if user is logged in and token is valid
    // This will redirect to login if token is expired
    if (!UserService.isLoggedIn()) {
      const loginUrl = `/login?original_url=${UserService.getCurrentLocation()}`;
      navigate(loginUrl, { replace: true });
    }
  }, [navigate]);

  return null;
}
