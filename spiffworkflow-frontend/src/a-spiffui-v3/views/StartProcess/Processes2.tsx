import React, { useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Paper,
  IconButton,
  Breadcrumbs,
  Link,
  Card,
  CardContent,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  InputAdornment,
} from '@mui/material';
import {
  Search,
  ExpandMore,
  Add,
  Edit,
  Delete,
  Home,
} from '@mui/icons-material';

function ProcessGroups() {
  const [searchQuery, setSearchQuery] = useState('');
  const [expanded, setExpanded] = useState('processGroups');

  const handleAccordionChange = (panel) => (event, isExpanded) => {
    setExpanded(isExpanded ? panel : false);
  };

  return (
    <Box sx={{ maxWidth: '1200px', margin: '0 auto', p: 3 }}>
      {/* Header */}
      <Typography variant="h4" sx={{ mb: 4 }}>
        Process Groups
      </Typography>

      {/* Search Bar */}
      <TextField
        fullWidth
        variant="outlined"
        placeholder="Search process groups..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <Search />
            </InputAdornment>
          ),
        }}
        sx={{ mb: 3 }}
      />

      {/* Breadcrumb */}
      <Breadcrumbs sx={{ mb: 3 }}>
        <Link
          underline="hover"
          sx={{ display: 'flex', alignItems: 'center' }}
          color="inherit"
          href="#"
        >
          <Home sx={{ mr: 0.5 }} fontSize="inherit" />
          Root
        </Link>
        <Link underline="hover" color="inherit" href="#">
          Site Administration
        </Link>
      </Breadcrumbs>

      {/* Main Content */}
      <Card>
        <CardContent>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              mb: 3,
            }}
          >
            <Typography variant="h5">
              Process Group: Site Administration
            </Typography>
            <Box>
              <IconButton>
                <Edit />
              </IconButton>
              <IconButton>
                <Delete />
              </IconButton>
            </Box>
          </Box>

          {/* Process Models Section */}
          <Accordion
            expanded={expanded === 'processModels'}
            onChange={handleAccordionChange('processModels')}
          >
            <AccordionSummary
              expandIcon={<ExpandMore />}
              sx={{
                '&:hover': { backgroundColor: 'action.hover' },
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  width: '100%',
                  pr: 2,
                }}
              >
                <Typography>Process Models (8)</Typography>
                <IconButton size="small" onClick={(e) => e.stopPropagation()}>
                  <Add />
                </IconButton>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              {/* Process Models content would go here */}
            </AccordionDetails>
          </Accordion>

          {/* Process Groups Section */}
          <Accordion
            expanded={expanded === 'processGroups'}
            onChange={handleAccordionChange('processGroups')}
          >
            <AccordionSummary
              expandIcon={<ExpandMore />}
              sx={{
                '&:hover': { backgroundColor: 'action.hover' },
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  width: '100%',
                  pr: 2,
                }}
              >
                <Typography>Process Groups (1)</Typography>
                <IconButton size="small" onClick={(e) => e.stopPropagation()}>
                  <Add />
                </IconButton>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
                  wut
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Groups: 0
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Models: 0
                </Typography>
              </Paper>
            </AccordionDetails>
          </Accordion>

          {/* Data Stores Section */}
          <Accordion
            expanded={expanded === 'dataStores'}
            onChange={handleAccordionChange('dataStores')}
          >
            <AccordionSummary
              expandIcon={<ExpandMore />}
              sx={{
                '&:hover': { backgroundColor: 'action.hover' },
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  width: '100%',
                  pr: 2,
                }}
              >
                <Typography>Data Stores (1)</Typography>
                <IconButton size="small" onClick={(e) => e.stopPropagation()}>
                  <Add />
                </IconButton>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              {/* Data Stores content would go here */}
            </AccordionDetails>
          </Accordion>
        </CardContent>
      </Card>
    </Box>
  );
}

export default ProcessGroups;
