import { ReactElement, useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Tile,
  // @ts-ignore
} from '@carbon/react';
import HttpService from '../services/HttpService';
import { ProcessModel, ProcessGroup } from '../interfaces';
import {
  modifyProcessIdentifierForPathParam,
  truncateString,
} from '../helpers';
import ProcessInstanceRun from './ProcessInstanceRun';

type OwnProps = {
  defaultProcessModels?: ProcessModel[];
  headerElement?: ReactElement;
  processGroup?: ProcessGroup;
  checkPermissions?: boolean;
  onLoadFunction?: Function;
  showNoItemsDisplayText?: boolean;
  userCanCreateProcessModels?: boolean;
};

export default function ProcessModelListTiles({
  defaultProcessModels,
  headerElement,
  processGroup,
  checkPermissions = true,
  onLoadFunction,
  showNoItemsDisplayText,
  userCanCreateProcessModels,
}: OwnProps) {
  const [searchParams] = useSearchParams();
  const [processModels, setProcessModels] = useState<ProcessModel[] | null>(
    null,
  );

  useEffect(() => {
    const setProcessModelsFromResult = (result: any) => {
      setProcessModels(result.results);
      if (onLoadFunction) {
        onLoadFunction(result);
      }
    };

    if (defaultProcessModels) {
      setProcessModels(defaultProcessModels);
    } else {
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
    }
  }, [searchParams, processGroup, onLoadFunction, defaultProcessModels]);

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
                <Link
                  title={row.id}
                  data-qa="process-model-show-link"
                  to={`/process-models/${modifyProcessIdentifierForPathParam(
                    row.id,
                  )}`}
                >
                  {row.display_name}
                </Link>
              </div>
              <p className="tile-description">
                {truncateString(row.description || '', 100)}
              </p>
              {row.primary_file_name ? (
                <ProcessInstanceRun
                  processModel={row}
                  className="tile-pin-bottom"
                  checkPermissions={checkPermissions}
                />
              ) : null}
            </div>
          </Tile>
        );
      });
    } else if (userCanCreateProcessModels) {
      displayText = (
        <p className="no-results-message">
          There are no process models to display. You can add one by clicking
          the &quot;Add a process model&quot; button. Process models will
          contain the bpmn diagrams and supporting files needed to create a
          runnable workflow.
        </p>
      );
    } else {
      displayText = (
        <p className="no-results-message">
          There are no process models to display
        </p>
      );
    }
    return displayText;
  };

  const processModelArea = () => {
    if (processModels && (showNoItemsDisplayText || processModels.length > 0)) {
      return (
        <>
          {headerElement}
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
