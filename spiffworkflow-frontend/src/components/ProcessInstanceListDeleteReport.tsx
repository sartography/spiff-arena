import { ProcessInstanceReport } from '../interfaces';
import HttpService from '../services/HttpService';
import ButtonWithConfirmation from './ButtonWithConfirmation';

type OwnProps = {
  onSuccess: (..._args: any[]) => any;
  processInstanceReportSelection: ProcessInstanceReport;
};

export default function ProcessInstanceListDeleteReport({
  onSuccess,
  processInstanceReportSelection,
}: OwnProps) {
  const deleteProcessInstanceReport = () => {
    HttpService.makeCallToBackend({
      path: `/process-instances/reports/${processInstanceReportSelection.id}`,
      successCallback: onSuccess,
      httpMethod: 'DELETE',
    });
  };

  return (
    <ButtonWithConfirmation
      description={`Delete Perspective ${processInstanceReportSelection.identifier}?`}
      onConfirmation={deleteProcessInstanceReport}
      buttonLabel="Delete"
    />
  );
}
