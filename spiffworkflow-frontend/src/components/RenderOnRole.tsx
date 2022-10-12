import React from 'react';
import UserService from '../services/UserService';

type Props = {
  roles: string[];
  children: React.ReactNode;
};

function RenderOnRole({ roles, children }: Props) {
  return UserService.hasRole(roles) ? children : null;
}

export default RenderOnRole;
