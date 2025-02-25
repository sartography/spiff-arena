import ProcessModelTreePage from './ProcessModelTreePage';
import { ProcessModelAction } from '../../interfaces';

export default function Processes({
  setNavElementCallback,
}: {
  setNavElementCallback: Function;
}) {
  return (
    <ProcessModelTreePage
      setNavElementCallback={setNavElementCallback}
      processModelAction={ProcessModelAction.Open}
      navigateToPage
    />
  );
}
