import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import UserService from '../services/UserService';

export default function LoginHandler() {
  const navigate = useNavigate();

  useEffect(() => {
    // Check if user is logged in and token is valid
    // This will redirect to login if token is expired
    if (!UserService.isLoggedIn()) {
      navigate(`/login?original_url=${UserService.getCurrentLocation()}`);
    }
  }, [navigate]);

  return null;
}
