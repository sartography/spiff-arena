import { Link } from 'react-router-dom';
import { modifyProcessIdentifierForPathParam } from '../helpers';
import { MessageInstance, ProcessInstance } from '../interfaces';

export function FormatProcessModelDisplayName(
  instanceObject: ProcessInstance | MessageInstance,
) {
  const {
    process_model_identifier: processModelIdentifier,
    process_model_display_name: processModelDisplayName,
  } = instanceObject;
  return (
    <Link
      to={`/process-models/${modifyProcessIdentifierForPathParam(
        processModelIdentifier,
      )}`}
      title={processModelIdentifier}
    >
      {processModelDisplayName}
    </Link>
  );
}
