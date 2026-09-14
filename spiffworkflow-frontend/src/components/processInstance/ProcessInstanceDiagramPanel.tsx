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
  modifiedProcessModelId?: string;
  onCallActivityNavigate: (task: BasicTask, event: any) => void;
  onDecisionNavigate?: (decisionId: string) => boolean;
  onElementClick: (shapeElement: any, bpmnProcessIdentifiers: any) => void;
};

export default function ProcessInstanceDiagramPanel({
  processInstance,
  tasks,
  tasksCallHadError,
  modifiedProcessModelId,
  onCallActivityNavigate,
  onElementClick,
  onDecisionNavigate,
}: ProcessInstanceDiagramPanelProps) {
  const { t } = useTranslation();
  if (!processInstance) {
    return null;
  }
  if (!tasks && !tasksCallHadError) {
    return <CircularProgress size={24} />;
  }

  const hasDiagramXml = !!processInstance.bpmn_xml_file_contents;
  const retrievalError =
    processInstance.bpmn_xml_file_contents_retrieval_error ||
    t('failed_to_load_diagram');

  if (!hasDiagramXml) {
    return (
      <Notification
        title={t('failed_to_load_diagram')}
        type="error"
        hideCloseButton
        allowTogglingFullMessage
      >
        <>
          {childrenForErrorObject(errorForDisplayFromString(retrievalError), t)}
        </>
      </Notification>
    );
  }

  return (
    <ReactDiagramEditor
      diagramType="readonly"
      diagramXML={processInstance.bpmn_xml_file_contents || ''}
      onCallActivityOverlayClick={onCallActivityNavigate}
      onLaunchDmnEditor={onDecisionNavigate}
      onElementClick={(shapeElement, processIdentifiers) => {
        const document = new DOMParser().parseFromString(
          processInstance.bpmn_xml_file_contents || '',
          'application/xml',
        );
        const task = Array.from(
          document.getElementsByTagNameNS('*', 'businessRuleTask'),
        ).find((element) => element.id === shapeElement.id);
        const decisionId =
          task?.getElementsByTagNameNS('*', 'calledDecisionId')[0]
            ?.textContent ||
          Array.from(task?.attributes || []).find(
            (attribute) => attribute.localName === 'decisionRef',
          )?.value;
        if (decisionId && onDecisionNavigate?.(decisionId)) {
          return;
        }
        onElementClick(shapeElement, processIdentifiers);
      }}
      modifiedProcessModelId={modifiedProcessModelId || ''}
      tasks={tasks}
    />
  );
}
