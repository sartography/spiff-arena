import { BrowserRouter } from 'react-router-dom';
import { defineAbility } from '@casl/ability';
import React from 'react';

import { AbilityContext } from './contexts/Can';
import UserService from './services/UserService';
import APIErrorProvider from './contexts/APIErrorContext';
import ContainerForExtensions from './ContainerForExtensions';

export default function App() {
  if (!UserService.isLoggedIn()) {
    UserService.doLogin();
    return null;
  }

  const ability = defineAbility(() => {});

  return (
    <div className="cds--white">
      {/* @ts-ignore */}
      <AbilityContext.Provider value={ability}>
        <APIErrorProvider>
          <BrowserRouter>
            <ContainerForExtensions />
          </BrowserRouter>
        </APIErrorProvider>
      </AbilityContext.Provider>
    </div>
  );
}
