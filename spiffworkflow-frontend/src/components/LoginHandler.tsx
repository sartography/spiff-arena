import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import UserService from '../services/UserService';

export default function LoginHandler() {
  const navigate = useNavigate();
  useEffect(() => {
    if (!UserService.isLoggedIn()) {
      navigate(`/login?original_url=${UserService.getCurrentLocation()}`);
    }
  }, [navigate]);
  return null;
}
