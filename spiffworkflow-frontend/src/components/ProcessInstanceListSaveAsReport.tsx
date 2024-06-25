import { useState } from 'react';
import {
  Button,
  TextInput,
  Stack,
  Modal,
  // @ts-ignore
} from '@carbon/react';
import { ProcessInstanceReport, ReportMetadata } from '../interfaces';
import HttpService from '../services/HttpService';

type OwnProps = {
  onSuccess: (..._args: any[]) => any;
  buttonText?: string;
  buttonClassName?: string;
  processInstanceReportSelection?: ProcessInstanceReport | null;
  reportMetadata: ReportMetadata | null;
};

export default function ProcessInstanceListSaveAsReport({
  onSuccess,
  processInstanceReportSelection,
  buttonClassName,
  buttonText = 'Salvar a Perspectiva',
  reportMetadata,
}: OwnProps) {
  const [identifier, setIdentifier] = useState<string>(
    processInstanceReportSelection?.identifier || '',
  );
  const [showSaveForm, setShowSaveForm] = useState<boolean>(false);

  const isEditMode = () => {
    return (
      processInstanceReportSelection &&
      processInstanceReportSelection.identifier === identifier
    );
  };

  const responseHandler = (result: any) => {
    if (result) {
      onSuccess(result, isEditMode() ? 'edit' : 'new');
    }
  };

  const handleSaveFormClose = () => {
    setIdentifier(processInstanceReportSelection?.identifier || '');
    setShowSaveForm(false);
  };

  const addProcessInstanceReport = (event: any) => {
    event.preventDefault();

    let path = `/process-instances/reports`;
    let httpMethod = 'POST';
    if (isEditMode() && processInstanceReportSelection) {
      httpMethod = 'PUT';
      path = `${path}/${processInstanceReportSelection.id}`;
    }

    HttpService.makeCallToBackend({
      path,
      successCallback: responseHandler,
      httpMethod,
      postBody: {
        identifier,
        report_metadata: reportMetadata,
      },
    });
    handleSaveFormClose();
  };

  let textInputComponent = null;
  textInputComponent = (
    <TextInput
      id="identifier"
      name="identifier"
      labelText="Identificador"
      className="no-wrap"
      inline
      value={identifier}
      onChange={(e: any) => setIdentifier(e.target.value)}
    />
  );

  let descriptionText =
    'Salve as colunas e filtros atuais como uma perspectiva para que você possa voltar a esta visualização no futuro.';
  if (processInstanceReportSelection) {
    descriptionText =
    'Mantenha o mesmo identificador e clique em Salvar para atualizar a perspectiva atual. Mude o identificador se quiser salvar a visualização atual com um novo nome.';  
  }

  return (
    <Stack gap={5} orientation="horizontal">
      <Modal
        open={showSaveForm}
        modalHeading="Salva Perspectiva"
        primaryButtonText="Salvar"
        primaryButtonDisabled={!identifier}
        onRequestSubmit={addProcessInstanceReport}
        onRequestClose={handleSaveFormClose}
        hasScrollingContent
        aria-label="save perspective"
      >
        <p className="data-table-description">{descriptionText}</p>
        {textInputComponent}
      </Modal>
      <Button
        kind="tertiary"
        className={buttonClassName}
        onClick={() => {
          setIdentifier(processInstanceReportSelection?.identifier || '');
          setShowSaveForm(true);
        }}
      >
        {buttonText}
      </Button>
    </Stack>
  );
}
