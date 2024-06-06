import { useEffect, useState } from 'react';
import {
  ComboBox,
  Grid,
  Column,
  FormLabel,
  // @ts-ignore
} from '@carbon/react';
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
      <Grid fullWidth condensed>
        <Column sm={2} md={3} lg={3}>
          <FormLabel className="with-top-margin">{titleText}</FormLabel>
        </Column>
        <Column sm={2} md={5} lg={13}>
          <ComboBox
            onChange={onChange}
            id="process-instance-report-select"
            data-qa="process-instance-report-selection"
            items={processInstanceReports}
            itemToString={(processInstanceReport: ProcessInstanceReport) => {
              if (processInstanceReport) {
                return reportSelectionString(processInstanceReport);
              }
              return null;
            }}
            shouldFilterItem={shouldFilterProcessInstanceReport}
            placeholder="Choose a process instance perspective"
            selectedItem={selectedItem}
          />
        </Column>
      </Grid>
    );
  }
  return null;
}
