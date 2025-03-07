import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Paper,
} from '@mui/material';
import appVersionInfo from '../helpers/appVersionInfo';
import { ObjectWithStringKeysAndValues } from '../interfaces';
import HttpService from '../services/HttpService';

function About() {
  const frontendVersionInfo = appVersionInfo();
  const [backendVersionInfo, setBackendVersionInfo] =
    useState<ObjectWithStringKeysAndValues | null>(null);

  useEffect(() => {
    const handleVersionInfoResponse = (
      response: ObjectWithStringKeysAndValues,
    ) => {
      setBackendVersionInfo(response);
    };

    HttpService.makeCallToBackend({
      path: `/debug/version-info`,
      successCallback: handleVersionInfoResponse,
    });
  }, []);

  const versionInfoFromDict = (
    title: string,
    versionInfoDict: ObjectWithStringKeysAndValues | null,
  ) => {
    if (versionInfoDict !== null && Object.keys(versionInfoDict).length) {
      const tableRows = Object.keys(versionInfoDict)
        .sort()
        .map((key) => (
          <TableRow key={key}>
            <TableCell>
              <strong>{key}</strong>
            </TableCell>
            <TableCell>{versionInfoDict[key]}</TableCell>
          </TableRow>
        ));
      return (
        <Box sx={{ mb: 2 }}>
          <Typography variant="h2" gutterBottom>
            {title}
          </Typography>
          <TableContainer component={Paper}>
            <Table>
              <TableBody>{tableRows}</TableBody>
            </Table>
          </TableContainer>
        </Box>
      );
    }
    return null;
  };

  return (
    <Box p={3}>
      <Typography variant="h1" gutterBottom>
        About
      </Typography>
      {versionInfoFromDict('Frontend version information', frontendVersionInfo)}
      {versionInfoFromDict('Backend version information', backendVersionInfo)}
    </Box>
  );
}

export default About;
