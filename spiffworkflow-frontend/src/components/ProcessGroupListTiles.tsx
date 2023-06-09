import { ReactElement, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  ArrowRight,
  // @ts-ignore
} from '@carbon/icons-react';
import {
  ClickableTile,
  // @ts-ignore
} from '@carbon/react';
import HttpService from '../services/HttpService';
import { ProcessGroup } from '../interfaces';
import {
  modifyProcessIdentifierForPathParam,
  truncateString,
} from '../helpers';

type OwnProps = {
  processGroup?: ProcessGroup;
  headerElement?: ReactElement;
};

export default function ProcessGroupListTiles({
  processGroup,
  headerElement,
}: OwnProps) {
  const [searchParams] = useSearchParams();

  const [processGroups, setProcessGroups] = useState<ProcessGroup[] | null>(
    null
  );

  useEffect(() => {
    const setProcessGroupsFromResult = (result: any) => {
      setProcessGroups(result.results);
    };
    let queryParams = '?per_page=1000';
    if (processGroup) {
      queryParams = `${queryParams}&process_group_identifier=${processGroup.id}`;
    }
    HttpService.makeCallToBackend({
      path: `/process-groups${queryParams}`,
      successCallback: setProcessGroupsFromResult,
    });
  }, [searchParams, processGroup]);

  const processGroupDirectChildrenCount = (pg: ProcessGroup) => {
    return (pg.process_models || []).length + (pg.process_groups || []).length;
  };

  const processGroupsDisplayArea = () => {
    let displayText = null;
    if (processGroups && processGroups.length > 0) {
      displayText = (processGroups || []).map((row: ProcessGroup) => {
        return (
          <ClickableTile
            id={`process-group-tile-${row.id}`}
            className="tile-process-group"
            href={`/admin/process-groups/${modifyProcessIdentifierForPathParam(
              row.id
            )}`}
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
    } else {
      displayText = <p>No Groups To Display</p>;
    }
    return displayText;
  };

  const processGroupArea = () => {
    if (processGroups && (!processGroup || processGroups.length > 0)) {
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
