import { Box, Container, Stack, Typography } from '@mui/material';
import { useEffect, useState } from 'react';
import { Subject, Subscription } from 'rxjs';
import useProcessGroups from '../../hooks/useProcessGroups';
import TreePanel from './TreePanel';
import SearchBar from './SearchBar';
import ProcessGroupCard from './ProcessGroupCard';
import ProcessModelCard from './ProcessModelCard';

export default function StartProcess() {
  const { processGroups } = useProcessGroups({ processInfo: {} });
  const [groups, setGroups] = useState<Record<string, any>[]>([]);
  const [models, setModels] = useState<Record<string, any>[]>([]);
  const clickStream = new Subject<Record<string, any>>();
  const gridProps = {
    width: '100%',
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, 400px)',
    justifyContent: 'center',
    gridGap: 20,
  };
  const dividerProps = {
    border: '0.5px solid',
    borderColor: 'borders.primary',
  };

  const handleClickStream = (group: Record<string, any>) => {
    if (group?.process_models) {
      setModels(group.process_models);
    }

    if (group?.process_groups) {
      setGroups(group.process_groups);
    }
  };

  useEffect(() => {
    if (processGroups?.results) {
      console.log(processGroups);
      setGroups(processGroups.results);
    }
  }, [processGroups]);

  let cardStreamSub: Subscription;
  useEffect(() => {
    if (!cardStreamSub && clickStream) {
      clickStream.subscribe(handleClickStream);
    }
  }, [clickStream]);

  return (
    <Container
      maxWidth={false}
      sx={{
        padding: '0px !important',
        overflow: 'hidden',
      }}
    >
      <Stack direction="row">
        <Box
          sx={{
            minWidth: 250,
            maxWidth: 450,
            width: '20%',
            paddingTop: 0.25,
          }}
        >
          <TreePanel processGroups={processGroups} stream={clickStream} />
        </Box>
        <Stack
          sx={{
            width: '100%',
          }}
        >
          <Stack
            gap={2}
            sx={{
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              padding: 2,
            }}
          >
            <SearchBar />

            <Stack
              gap={4}
              sx={{
                padding: 2,
                width: '100%',
                height: 'calc(100vh - 185px)',
                overflowY: 'auto',
                overflowX: 'hidden',
              }}
            >
              <Stack gap={1} sx={{ width: '100%' }}>
                <Typography variant="h6">Process Models</Typography>
                <Box sx={dividerProps} />
              </Stack>
              <Box sx={gridProps}>
                {models.map((model: Record<string, any>) => (
                  <ProcessModelCard model={model} stream={clickStream} />
                ))}
              </Box>

              <Stack gap={1} sx={{ width: '100%' }}>
                <Typography variant="h6">Process Groups</Typography>
                <Box sx={dividerProps} />
              </Stack>
              <Box sx={gridProps}>
                {groups.map((group: Record<string, any>) => (
                  <ProcessGroupCard group={group} stream={clickStream} />
                ))}
              </Box>
            </Stack>
          </Stack>
        </Stack>
      </Stack>
    </Container>
  );
}
