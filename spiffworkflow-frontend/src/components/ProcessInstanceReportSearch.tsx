import { useEffect, useState } from 'react';
import {
  ComboBox,
  Stack,
  FormLabel,
  // @ts-ignore
} from '@carbon/react';
import { truncateString } from '../helpers';
import { ProcessInstanceReport } from '../interfaces';
import HttpService from '../services/HttpService';

type OwnProps = {
  onChange: (..._args: any[]) => any;
  selectedItem?: ProcessInstanceReport | null;
  titleText?: string;
};

export default function ProcessInstanceReportSearch({
  selectedItem,
  onChange,
  titleText = 'Process instance perspectives',
}: OwnProps) {
  const [processInstanceReports, setProcessInstanceReports] = useState<
    ProcessInstanceReport[] | null
  >(null);

  useEffect(() => {
    function setProcessInstanceReportsFromResult(
      result: ProcessInstanceReport[]
    ) {
      setProcessInstanceReports(result);
    }

    setProcessInstanceReports([]);
    HttpService.makeCallToBackend({
      path: `/process-instances/reports`,
      successCallback: setProcessInstanceReportsFromResult,
    });
  }, []);

  const reportSelectionString = (
    processInstanceReport: ProcessInstanceReport
  ) => {
    return `${truncateString(processInstanceReport.identifier, 20)} (Id: ${
      processInstanceReport.id
    })`;
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
      <Stack orientation="horizontal" gap={2}>
        <FormLabel className="with-top-margin">{titleText}</FormLabel>
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
      </Stack>
    );
  }
  return null;
}
