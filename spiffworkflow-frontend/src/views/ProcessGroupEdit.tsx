import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
// @ts-ignore
import { Box, Typography } from '@mui/material';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';
import ProcessGroupForm from '../components/ProcessGroupForm';
import { ProcessGroup } from '../interfaces';
import { setPageTitle } from '../helpers';

export default function ProcessGroupEdit() {
  const params = useParams();
  const [processGroup, setProcessGroup] = useState<ProcessGroup | null>(null);

  useEffect(() => {
    const setProcessGroupsFromResult = (result: any) => {
      setProcessGroup(result);
    };

    HttpService.makeCallToBackend({
      path: `/process-groups/${params.process_group_id}`,
      successCallback: setProcessGroupsFromResult,
    });
  }, [params.process_group_id]);

  if (processGroup) {
    setPageTitle([`Editing ${processGroup.display_name}`]);
    return (
      <>
        <ProcessBreadcrumb
          hotCrumbs={[
            ['Process Groups', '/process-groups'],
            {
              entityToExplode: processGroup,
              entityType: 'process-group',
              linkLastItem: true,
            },
          ]}
        />
        <Typography variant="h1">
          Edit Process Group: {(processGroup as any).id}
        </Typography>
        <Box mt={2}>
          <ProcessGroupForm
            mode="edit"
            processGroup={processGroup}
            setProcessGroup={setProcessGroup}
          />
        </Box>
      </>
    );
  }
  return null;
}
