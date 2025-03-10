import { useState, useEffect, useCallback, useRef } from 'react';
import HttpService from '../services/HttpService';
import DateAndTimeService from '../services/DateAndTimeService';
import { refreshAtInterval } from '../helpers';
import {
  PaginationObject,
  ProcessInstance,
  ReportMetadata,
  ReportFilter,
  ProcessInstanceReport,
} from '../interfaces';

type OwnProps = {
  reportIdentifier: string;
  additionalReportFilters?: ReportFilter[];
  autoReload?: boolean;
};

const useProcessInstances = ({
  reportIdentifier,
  additionalReportFilters,
  autoReload = false,
}: OwnProps) => {
  const [processInstances, setProcessInstances] = useState<ProcessInstance[]>(
    [],
  );
  const [pagination, setPagination] = useState<PaginationObject | null>(null);
  const [reportMetadata, setReportMetadata] = useState<ReportMetadata | null>(
    null,
  );
  const clearRefreshRef = useRef<any>(null);

  const stopRefreshing = useCallback((error: any) => {
    if (clearRefreshRef.current) {
      clearRefreshRef.current();
    }
    if (error) {
      console.error(error);
    }
  }, []);

  const setProcessInstancesFromResult = useCallback((result: any) => {
    setProcessInstances(result.results);
    setPagination(result.pagination);
    setReportMetadata(result.report_metadata);
  }, []);

  const getProcessInstances = useCallback(
    (currentReportMetadata: ReportMetadata | null | undefined = null) => {
      const reportMetadataToUse = currentReportMetadata || {
        columns: [],
        filter_by: [],
        order_by: [],
      };

      if (additionalReportFilters) {
        additionalReportFilters.forEach((arf: ReportFilter) => {
          const existingFilterIndex = reportMetadataToUse.filter_by.findIndex(
            (existing) => existing.field_name === arf.field_name,
          );
          if (existingFilterIndex === -1) {
            reportMetadataToUse.filter_by.push(arf);
          } else {
            reportMetadataToUse.filter_by[existingFilterIndex] = arf;
          }
        });
      }

      const queryParamString = `per_page=1000&page=1`;
      HttpService.makeCallToBackend({
        path: `/process-instances/for-me?${queryParamString}`,
        successCallback: setProcessInstancesFromResult,
        httpMethod: 'POST',
        failureCallback: stopRefreshing,
        onUnauthorized: stopRefreshing,
        postBody: {
          report_metadata: reportMetadataToUse,
        },
      });
    },
    [additionalReportFilters, setProcessInstancesFromResult, stopRefreshing],
  );

  useEffect(() => {
    const setReportMetadataFromReport = (
      processInstanceReport: ProcessInstanceReport,
    ) => {
      getProcessInstances(processInstanceReport.report_metadata);
    };

    const checkForReportAndRun = () => {
      if (reportIdentifier) {
        const queryParamString = `?report_identifier=${reportIdentifier}`;
        HttpService.makeCallToBackend({
          path: `/process-instances/report-metadata${queryParamString}`,
          successCallback: setReportMetadataFromReport,
          onUnauthorized: () => stopRefreshing,
        });
      } else {
        getProcessInstances();
      }
    };

    checkForReportAndRun();

    if (autoReload) {
      clearRefreshRef.current = refreshAtInterval(
        DateAndTimeService.REFRESH_INTERVAL_SECONDS,
        DateAndTimeService.REFRESH_TIMEOUT_SECONDS,
        checkForReportAndRun,
      );
      return clearRefreshRef.current;
    }
    return undefined;
  }, [autoReload, getProcessInstances, reportIdentifier, stopRefreshing]);

  return { processInstances, pagination, reportMetadata };
};

export default useProcessInstances;
