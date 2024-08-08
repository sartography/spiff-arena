import { useState, useEffect, useCallback, useRef } from 'react';
import HttpService from '../services/HttpService';
import DateAndTimeService from '../services/DateAndTimeService';
import { refreshAtInterval } from '../helpers';
import {
  PaginationObject,
  ProcessInstance,
  ReportMetadata,
  ReportFilter,
} from '../interfaces';

const useProcessInstances = (
  reportIdentifier: string,
  additionalReportFilters?: ReportFilter[],
  paginationQueryParamPrefix?: string,
  perPageOptions?: number[],
  autoReload = false,
) => {
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

  const getProcessInstances = useCallback(() => {
    const reportMetadataToUse: ReportMetadata = {
      columns: [],
      filter_by: [],
      order_by: [],
    };

    if (additionalReportFilters) {
      additionalReportFilters.forEach((arf: ReportFilter) => {
        if (!reportMetadataToUse.filter_by.includes(arf)) {
          reportMetadataToUse.filter_by.push(arf);
        }
      });
    }

    const queryParamString = `per_page=${perPageOptions ? perPageOptions[1] : 5}&page=1`;
    HttpService.makeCallToBackend({
      path: `/process-instances?${queryParamString}`,
      successCallback: setProcessInstancesFromResult,
      httpMethod: 'POST',
      failureCallback: stopRefreshing,
      onUnauthorized: stopRefreshing,
      postBody: {
        report_metadata: reportMetadataToUse,
      },
    });
  }, [
    additionalReportFilters,
    perPageOptions,
    setProcessInstancesFromResult,
    stopRefreshing,
  ]);

  useEffect(() => {
    const setReportMetadataFromReport = (processInstanceReport: any) => {
      getProcessInstances();
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
