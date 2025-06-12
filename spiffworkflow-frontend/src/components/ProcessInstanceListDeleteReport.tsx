import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation();
  const deleteProcessInstanceReport = () => {
    HttpService.makeCallToBackend({
      path: `/process-instances/reports/${processInstanceReportSelection.id}`,
      successCallback: onSuccess,
      httpMethod: 'DELETE',
    });
  };

  return (
    <ButtonWithConfirmation
      description={t('delete_perspective_confirmation', { identifier: processInstanceReportSelection.identifier })}
      onConfirmation={deleteProcessInstanceReport}
      buttonLabel={t('delete')}
    />
  );
}
