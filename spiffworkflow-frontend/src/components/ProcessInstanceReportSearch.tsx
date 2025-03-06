import { useEffect, useState } from 'react';
import { Autocomplete, Grid, FormLabel, TextField } from '@mui/material';
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
  titleText = 'Process instance perspectives',
}: OwnProps) {
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
      <Grid container spacing={2} style={{ paddingTop: '0px' }}>
        <Grid item xs={12} sm={6} md={12}>
          <FormLabel>{titleText}</FormLabel>
          <Autocomplete
            onChange={(_, value) => onChange(value)}
            id="process-instance-report-select"
            data-qa="process-instance-report-selection"
            options={processInstanceReports || []}
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
                fullWidth
                inputProps={params.inputProps}
                placeholder="Choose a process instance perspective"
                slotProps={{
                  input: params.InputProps,
                  htmlInput: params.inputProps,
                  inputLabel: { shrink: true },
                }}
              />
            )}
            value={selectedItem}
          />
        </Grid>
      </Grid>
    );
  }
  return null;
}
