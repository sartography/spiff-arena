import ProcessModelTreePage from './ProcessModelTreePage';
import { ProcessModelAction } from '../../interfaces';

type OwnProps = {
  setNavElementCallback: Function;
};
/**
 * Top level layout and control container for this view,
 * feeds various streams, data and callbacks to children.
 */
export default function StartProcess({ setNavElementCallback }: OwnProps) {
  return (
    <ProcessModelTreePage
      setNavElementCallback={setNavElementCallback}
      processModelAction={ProcessModelAction.StartProcess}
    />
  );
}
