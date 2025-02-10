import ProcessModelTreePage from './ProcessModelTreePage';
import { ProcessModelAction } from '../../interfaces';
import {useEffect} from 'react';
import {TreePanel} from './TreePanel';

export default function Processes({setNavElementCallback}: {setNavElementCallback: Function}) {

  useEffect(() => {
    if (setNavElementCallback) {
      setNavElementCallback(
        <TreePanel
          processGroups={[]}
        />,
      );
    }
  }, [setNavElementCallback]);

  return (
    <ProcessModelTreePage
      processModelAction={ProcessModelAction.Open}
      navigateToPage
    />
  );
}
