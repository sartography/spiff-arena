import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Container,
  Stack,
} from '@mui/material';
import { useEffect, useState } from 'react';
import { Subject, Subscription } from 'rxjs';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import useProcessGroups from '../../hooks/useProcessGroups';
import TreePanel from './TreePanel';
import SearchBar from './SearchBar';
import ProcessGroupCard from './ProcessGroupCard';
import ProcessModelCard from './ProcessModelCard';

export default function StartProcess() {
  const { processGroups } = useProcessGroups({ processInfo: {} });
  const [groups, setGroups] = useState<Record<string, any>[]>([]);
  const [models, setModels] = useState<Record<string, any>[]>([]);
  // On load, there are always groups and never models, expand accordingly.
  const [groupsExpanded, setGroupsExpanded] = useState(true);
  const [modelsExpanded, setModelsExpanded] = useState(false);
  const clickStream = new Subject<Record<string, any>>();
  const gridProps = {
    width: '100%',
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, 400px)',
    justifyContent: 'center',
    gridGap: 20,
  };

  const handleClickStream = (group: Record<string, any>) => {
    if (group?.process_models) {
      // If a user clicks a group, and it has models, expand them for the user.
      if (group.process_models.length) {
        setModelsExpanded(true);
      }
      setModels(group.process_models);
    }

    if (group?.process_groups) {
      setGroups(group.process_groups);
    }
  };

  useEffect(() => {
    if (processGroups?.results) {
      setGroups(processGroups.results);
      setGroupsExpanded(!!processGroups.results.length);
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
            }}
          >
            <Box sx={{ width: '100%', padding: 2 }}>
              <SearchBar />
            </Box>

            <Stack
              sx={{
                width: '100%',
                height: 'calc(100vh - 205px)',
                overflowY: 'auto',
                overflowX: 'hidden',
                padding: 0,
              }}
            >
              <Stack
                gap={4}
                sx={{
                  padding: 2,
                }}
              >
                <Accordion
                  expanded={modelsExpanded}
                  onChange={() => setModelsExpanded((prev) => !prev)}
                >
                  <AccordionSummary
                    expandIcon={<ExpandMoreIcon />}
                    aria-controls="Process Models Accordion"
                  >
                    ({models.length}) Process Models
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box sx={gridProps}>
                      {models.map((model: Record<string, any>) => (
                        <ProcessModelCard model={model} stream={clickStream} />
                      ))}
                    </Box>
                  </AccordionDetails>
                </Accordion>
                <Accordion
                  expanded={groupsExpanded}
                  onChange={() => setGroupsExpanded((prev) => !prev)}
                >
                  <AccordionSummary
                    expandIcon={<ExpandMoreIcon />}
                    aria-controls="Process Groups Accordion"
                  >
                    ({groups.length}) Process Groups
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box sx={gridProps}>
                      {groups.map((group: Record<string, any>) => (
                        <ProcessGroupCard group={group} stream={clickStream} />
                      ))}
                    </Box>
                  </AccordionDetails>
                </Accordion>
              </Stack>
            </Stack>
          </Stack>
        </Stack>
      </Stack>
    </Container>
  );
}
