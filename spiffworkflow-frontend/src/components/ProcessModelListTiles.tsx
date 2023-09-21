import { ReactElement, useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Tile,
  // @ts-ignore
} from '@carbon/react';
import HttpService from '../services/HttpService';
import { ProcessModel, ProcessInstance, ProcessGroup } from '../interfaces';
import {
  modifyProcessIdentifierForPathParam,
  truncateString,
} from '../helpers';
import ProcessInstanceRun from './ProcessInstanceRun';
import { Notification } from './Notification';

type OwnProps = {
  headerElement?: ReactElement;
  processGroup?: ProcessGroup;
  checkPermissions?: boolean;
};

export default function ProcessModelListTiles({
  headerElement,
  processGroup,
  checkPermissions = true,
}: OwnProps) {
  const [searchParams] = useSearchParams();
  const [processModels, setProcessModels] = useState<ProcessModel[] | null>(
    null
  );
  const [processInstance, setProcessInstance] =
    useState<ProcessInstance | null>(null);

  useEffect(() => {
    const setProcessModelsFromResult = (result: any) => {
      setProcessModels(result.results);
    };
    // only allow 10 for now until we get the backend only returning certain models for user execution
    let queryParams = '?per_page=1000';
    if (processGroup) {
      queryParams = `${queryParams}&process_group_identifier=${processGroup.id}`;
    } else {
      queryParams = `${queryParams}&recursive=true&filter_runnable_by_user=true`;
    }
    HttpService.makeCallToBackend({
      path: `/process-models${queryParams}`,
      successCallback: setProcessModelsFromResult,
    });
  }, [searchParams, processGroup]);

  const processInstanceRunResultTag = () => {
    if (processInstance) {
      return (
        <Notification
          title={`Process Instance ${processInstance.id} kicked off`}
          onClose={() => setProcessInstance(null)}
        >
          <Link
            to={`/process-instances/${modifyProcessIdentifierForPathParam(
              processInstance.process_model_identifier
            )}/${processInstance.id}`}
            data-qa="process-instance-show-link"
          >
            view
          </Link>
        </Notification>
      );
    }
    return null;
  };

  const processModelsDisplayArea = () => {
    let displayText = null;
    if (processModels && processModels.length > 0) {
      displayText = (processModels || []).map((row: ProcessModel) => {
        return (
          <Tile
            id={`process-model-tile-${row.id}`}
            className="tile-process-group"
          >
            <div className="tile-process-group-content-container">
              <div className="tile-title-top">
                <a
                  title={row.id}
                  data-qa="process-model-show-link"
                  href={`/process-models/${modifyProcessIdentifierForPathParam(
                    row.id
                  )}`}
                >
                  {row.display_name}
                </a>
              </div>
              <p className="tile-description">
                {truncateString(row.description || '', 100)}
              </p>
              <ProcessInstanceRun
                processModel={row}
                onSuccessCallback={setProcessInstance}
                className="tile-pin-bottom"
                checkPermissions={checkPermissions}
              />
            </div>
          </Tile>
        );
      });
    } else {
      displayText = <p>No Models To Display</p>;
    }
    return displayText;
  };

  const processModelArea = () => {
    if (processModels && processModels.length > 0) {
      return (
        <>
          {headerElement}
          {processInstanceRunResultTag()}
          {processModelsDisplayArea()}
        </>
      );
    }
    return null;
  };

  if (processModels) {
    return <>{processModelArea()}</>;
  }
  return null;
}
