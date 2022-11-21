import { useState } from 'react';
import {
  ComboBox,
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
  titleText = 'Process instance reports',
}: OwnProps) {
  const [processInstanceReports, setProcessInstanceReports] = useState<
    ProcessInstanceReport[] | null
  >(null);

  function setProcessInstanceReportsFromResult(result: any) {
    const processInstanceReportsFromApi = result.map((item: any) => {
      return { id: item.identifier, display_name: item.identifier };
    });
    setProcessInstanceReports(processInstanceReportsFromApi);
  }

  if (processInstanceReports === null) {
    setProcessInstanceReports([]);
    HttpService.makeCallToBackend({
      path: `/process-instances/reports`,
      successCallback: setProcessInstanceReportsFromResult,
    });
  }

  const shouldFilterProcessInstanceReport = (options: any) => {
    const processInstanceReport: ProcessInstanceReport = options.item;
    const { inputValue } = options;
    return `${processInstanceReport.id} (${processInstanceReport.display_name})`.includes(
      inputValue
    );
  };

  const reportsAvailable = () => {
    return processInstanceReports && processInstanceReports.length > 0;
  }

  return reportsAvailable() ? (
    <ComboBox
      onChange={onChange}
      id="process-instance-report-select"
      data-qa="process-instance-report-selection"
      items={processInstanceReports}
      itemToString={(processInstanceReport: ProcessInstanceReport) => {
        if (processInstanceReport) {
          return `${processInstanceReport.id} (${truncateString(
            processInstanceReport.display_name,
            20
          )})`;
        }
        return null;
      }}
      shouldFilterItem={shouldFilterProcessInstanceReport}
      placeholder="Choose a process instance report"
      titleText={titleText}
      selectedItem={selectedItem}
    />
  ) : null;
}
