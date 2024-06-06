import { ReactElement, useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowRight } from '@carbon/icons-react';
import { ClickableTile } from '@carbon/react';
import HttpService from '../services/HttpService';
import { ProcessGroup } from '../interfaces';
import {
  modifyProcessIdentifierForPathParam,
  truncateString,
} from '../helpers';

type OwnProps = {
  defaultProcessGroups?: ProcessGroup[];
  processGroup?: ProcessGroup;
  headerElement?: ReactElement;
  showNoItemsDisplayText?: boolean;
  userCanCreateProcessModels?: boolean;
};

export default function ProcessGroupListTiles({
  defaultProcessGroups,
  processGroup,
  headerElement,
  showNoItemsDisplayText,
  userCanCreateProcessModels,
}: OwnProps) {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [processGroups, setProcessGroups] = useState<ProcessGroup[] | null>(
    null,
  );

  useEffect(() => {
    const setProcessGroupsFromResult = (result: any) => {
      setProcessGroups(result.results);
    };

    if (defaultProcessGroups) {
      setProcessGroups(defaultProcessGroups);
    } else {
      let queryParams = '?per_page=1000';
      if (processGroup) {
        queryParams = `${queryParams}&process_group_identifier=${processGroup.id}`;
      }
      HttpService.makeCallToBackend({
        path: `/process-groups${queryParams}`,
        successCallback: setProcessGroupsFromResult,
      });
    }
  }, [searchParams, processGroup, defaultProcessGroups]);

  const processGroupDirectChildrenCount = (pg: ProcessGroup) => {
    return (pg.process_models || []).length + (pg.process_groups || []).length;
  };

  const navigateToProcessGroup = (url: string) => {
    navigate(url);
  };

  const processGroupsDisplayArea = () => {
    let displayText = null;
    if (processGroups && processGroups.length > 0) {
      displayText = (processGroups || []).map((row: ProcessGroup) => {
        return (
          <ClickableTile
            id={`process-group-tile-${row.id}`}
            key={`process-group-tile-${row.id}`}
            className="tile-process-group"
            onClick={() =>
              navigateToProcessGroup(
                `/process-groups/${modifyProcessIdentifierForPathParam(row.id)}`,
              )
            }
          >
            <div className="tile-process-group-content-container">
              <ArrowRight />
              <div className="tile-process-group-display-name">
                {row.display_name}
              </div>
              <p className="tile-description">
                {truncateString(row.description || '', 100)}
              </p>
              <p className="tile-process-group-children-count tile-pin-bottom">
                Total Sub Items: {processGroupDirectChildrenCount(row)}
              </p>
            </div>
          </ClickableTile>
        );
      });
    } else if (userCanCreateProcessModels) {
      displayText = (
        <p className="no-results-message">
          There are no process groups to display. You can add one by clicking
          the &quot;Add a process group&quot; button. Process groups can contain
          additional process groups and / or process models.
        </p>
      );
    } else {
      displayText = (
        <p className="no-results-message">
          There are no process groups to display
        </p>
      );
    }
    return displayText;
  };

  const processGroupArea = () => {
    if (processGroups && (showNoItemsDisplayText || processGroups.length > 0)) {
      return (
        <>
          {headerElement}
          {processGroupsDisplayArea()}
        </>
      );
    }
    return null;
  };

  if (processGroups) {
    return (
      <>
        {/* so we can check if the groups have loaded in cypress tests */}
        <div data-qa="process-groups-loaded" className="hidden" />
        {processGroupArea()}
      </>
    );
  }
  return null;
}
