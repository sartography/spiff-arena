import { CircularProgress } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { BasicTask, ProcessInstance } from '../../interfaces';
import ReactDiagramEditor from '../ReactDiagramEditor';
import { Notification } from '../Notification';
import {
  childrenForErrorObject,
  errorForDisplayFromString,
} from '../ErrorDisplay';

type ProcessInstanceDiagramPanelProps = {
  processInstance: ProcessInstance | null;
  tasks: BasicTask[] | null;
  tasksCallHadError: boolean;
  diagramFileName: string | null;
  diagramProcessModelId: string | null;
  diagramLoadError: string | null;
  modifiedProcessModelId?: string;
  onCallActivityNavigate: (task: BasicTask, event: any) => void;
  onElementClick: (shapeElement: any, bpmnProcessIdentifiers: any) => void;
};

export default function ProcessInstanceDiagramPanel({
  processInstance,
  tasks,
  tasksCallHadError,
  diagramFileName,
  diagramProcessModelId,
  diagramLoadError,
  modifiedProcessModelId,
  onCallActivityNavigate,
  onElementClick,
}: ProcessInstanceDiagramPanelProps) {
  const { t } = useTranslation();
  if (!processInstance) {
    return null;
  }
  if (!tasks && !tasksCallHadError) {
    return <CircularProgress size={24} />;
  }

  const hasDiagramXml = !!processInstance.bpmn_xml_file_contents;
  const canLoadFromModel =
    !!diagramFileName && !!diagramProcessModelId && !hasDiagramXml;
  const retrievalError =
    processInstance.bpmn_xml_file_contents_retrieval_error || '';

  if (
    !hasDiagramXml &&
    !canLoadFromModel &&
    (diagramLoadError || retrievalError)
  ) {
    return (
      <Notification
        title={t('failed_to_load_diagram')}
        type="error"
        hideCloseButton
        allowTogglingFullMessage
      >
        <>
          {childrenForErrorObject(
            errorForDisplayFromString(diagramLoadError || retrievalError),
            t,
          )}
        </>
      </Notification>
    );
  }

  return (
    <ReactDiagramEditor
      diagramType="readonly"
      diagramXML={processInstance.bpmn_xml_file_contents || ''}
      fileName={canLoadFromModel ? diagramFileName || undefined : undefined}
      onCallActivityOverlayClick={onCallActivityNavigate}
      onElementClick={onElementClick}
      modifiedProcessModelId={
        canLoadFromModel
          ? diagramProcessModelId || ''
          : modifiedProcessModelId || ''
      }
      tasks={tasks}
    />
  );
}
