import ProcessModelTreePage from './ProcessModelTreePage';
import { ProcessModelAction } from '../../interfaces';

export default function Processes() {
  return <ProcessModelTreePage processModelAction={ProcessModelAction.Open} />;
}
