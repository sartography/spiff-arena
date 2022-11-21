import { ReactElement, useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Tile,
  // @ts-ignore
} from '@carbon/react';
import HttpService from '../services/HttpService';
import { ProcessModel, ProcessInstance } from '../interfaces';
import { modifyProcessModelPath, truncateString } from '../helpers';
import ProcessInstanceRun from './ProcessInstanceRun';

type OwnProps = {
  headerElement?: ReactElement;
};

export default function ProcessModelListTiles({ headerElement }: OwnProps) {
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
    // only allow 10 for now until we get the backend only returnin certain models for user execution
    const queryParams = '?per_page=10';
    HttpService.makeCallToBackend({
      path: `/process-models${queryParams}`,
      successCallback: setProcessModelsFromResult,
    });
  }, [searchParams]);

  const processInstanceRunResultTag = () => {
    if (processInstance) {
      return (
        <div className="alert alert-success" role="alert">
          <p>
            Process Instance {processInstance.id} kicked off (
            <Link
              to={`/admin/process-models/${modifyProcessModelPath(
                processInstance.process_model_identifier
              )}/process-instances/${processInstance.id}`}
              data-qa="process-instance-show-link"
            >
              view
            </Link>
            ).
          </p>
        </div>
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
            id="tile-1"
            className="tile-process-group"
            href={`/admin/process-models/${modifyProcessModelPath(row.id)}`}
          >
            <div className="tile-process-group-content-container">
              <div className="tile-title-top">{row.display_name}</div>
              <p className="tile-description">
                {truncateString(row.description || '', 25)}
              </p>
              <ProcessInstanceRun
                processModel={row}
                onSuccessCallback={setProcessInstance}
                className="tile-pin-bottom"
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
