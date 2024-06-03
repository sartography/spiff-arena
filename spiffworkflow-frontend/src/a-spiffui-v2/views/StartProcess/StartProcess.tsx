import { Box, Container, Divider, Stack, Typography } from '@mui/material';
import { useEffect } from 'react';
import useProcessGroups from '../../hooks/useProcessGroups';
import TreePanel from './TreePanel';
import SearchBar from './SearchBar';
import ProcessGroupCard from './ProcessGroupCard';

export default function StartProcess() {
  const { processGroups } = useProcessGroups({ processInfo: {} });

  useEffect(() => {
    console.log(processGroups);
  }, [processGroups]);

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
          <TreePanel processGroups={processGroups} />
        </Box>
        <Stack
          sx={{
            padding: 2,
            width: '100%',
          }}
        >
          <Stack
            gap={4}
            sx={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <SearchBar />

            <Stack gap={1} sx={{ width: '100%' }}>
              <Typography variant="h6">Favorites</Typography>
              <Box
                sx={{
                  border: '0.5px solid',
                  borderColor: 'borders.primary',
                }}
              />
            </Stack>

            <Stack gap={1} sx={{ width: '100%' }}>
              <Typography variant="h6">Process Groups</Typography>
              <Box
                sx={{
                  border: '0.5px solid',
                  borderColor: 'borders.primary',
                }}
              />
            </Stack>

            <Box
              sx={{
                width: '100%',
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, 400px)',
                justifyContent: 'center',
                gridGap: 20,
              }}
            >
              {processGroups?.results?.map((group: Record<string, any>) => (
                <ProcessGroupCard group={group} />
              ))}
            </Box>
          </Stack>
        </Stack>
      </Stack>
    </Container>
  );
}
