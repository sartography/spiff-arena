import { useNavigate } from 'react-router-dom';
import { ProcessInstanceReport } from '../interfaces';
import HttpService from '../services/HttpService';
import ButtonWithConfirmation from './ButtonWithConfirmation';

type OwnProps = {
  processInstanceReportSelection: ProcessInstanceReport;
};

export default function ProcessInstanceListDeleteReport({
  processInstanceReportSelection,
}: OwnProps) {
  const navigate = useNavigate();

  const navigateToProcessInstances = (_result: any) => {
    navigate(`/admin/process-instances`);
  };

  const deleteProcessInstanceReport = () => {
    HttpService.makeCallToBackend({
      path: `/process-instances/reports/${processInstanceReportSelection.id}`,
      successCallback: navigateToProcessInstances,
      httpMethod: 'DELETE',
    });
  };

  return (
    <ButtonWithConfirmation
      description={`Delete Report ${processInstanceReportSelection.identifier}?`}
      onConfirmation={deleteProcessInstanceReport}
      buttonLabel="Delete"
    />
  );
}
