import { defineAbility } from '@casl/ability';
import React from 'react';

import { AbilityContext } from './contexts/Can';
import APIErrorProvider from './contexts/APIErrorContext';
import ContainerForExtensions from './ContainerForExtensions';

export default function App() {
  const ability = defineAbility(() => {});
  return (
    <div className="cds--white">
      <APIErrorProvider>
        <AbilityContext.Provider value={ability}>
          <ContainerForExtensions />
        </AbilityContext.Provider>
      </APIErrorProvider>
    </div>
  );
}
