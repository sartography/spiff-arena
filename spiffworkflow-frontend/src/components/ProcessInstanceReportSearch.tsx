import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Autocomplete, TextField } from '@mui/material';
import { ProcessInstanceReport } from '../interfaces';
import HttpService from '../services/HttpService';

type OwnProps = {
  onChange: (..._args: any[]) => any;
  selectedItem?: ProcessInstanceReport | null;
  titleText?: string;
  selectedReportId?: string | null;
  handleSetSelectedReportCallback?: Function;
};

export default function ProcessInstanceReportSearch({
  selectedItem,
  onChange,
  selectedReportId,
  handleSetSelectedReportCallback,
  titleText = undefined,
}: OwnProps) {
  const { t } = useTranslation();
  const [processInstanceReports, setProcessInstanceReports] = useState<
    ProcessInstanceReport[] | null
  >(null);

  useEffect(() => {
    const selectedReportIdAsNumber = Number(selectedReportId);

    function setProcessInstanceReportsFromResult(
      result: ProcessInstanceReport[],
    ) {
      setProcessInstanceReports(result);
      if (selectedReportId && handleSetSelectedReportCallback) {
        result.forEach((processInstanceReport: ProcessInstanceReport) => {
          if (processInstanceReport.id === selectedReportIdAsNumber) {
            handleSetSelectedReportCallback(processInstanceReport);
          }
        });
      }
    }

    HttpService.makeCallToBackend({
      path: `/process-instances/reports`,
      successCallback: setProcessInstanceReportsFromResult,
    });
  }, [handleSetSelectedReportCallback, selectedReportId]);

  const reportSelectionString = (
    processInstanceReport: ProcessInstanceReport,
  ) => {
    return `${processInstanceReport.identifier} (Id: ${processInstanceReport.id})`;
  };

  const shouldFilterProcessInstanceReport = (options: any) => {
    const processInstanceReport: ProcessInstanceReport = options.item;
    const { inputValue } = options;
    return reportSelectionString(processInstanceReport).includes(inputValue);
  };

  const reportsAvailable = () => {
    return processInstanceReports && processInstanceReports.length > 0;
  };

  if (reportsAvailable()) {
    return (
      <Autocomplete
        onChange={(_, value) => onChange(value)}
        id="process-instance-report-select"
        data-testid="process-instance-report-selection"
        options={processInstanceReports || []}
        fullWidth
        size="small"
        getOptionLabel={(processInstanceReport: ProcessInstanceReport) => {
          if (processInstanceReport) {
            return reportSelectionString(processInstanceReport);
          }
          return '';
        }}
        filterOptions={(options, state) =>
          options.filter((option) =>
            shouldFilterProcessInstanceReport({
              item: option,
              inputValue: state.inputValue,
            }),
          )
        }
        renderInput={(params) => (
          <TextField
            {...params}
            fullWidth
            label={titleText || t('process_perspectives')}
            placeholder={t('choose_process_instance_perspective')}
          />
        )}
        value={selectedItem}
      />
    );
  }
  return null;
}
