// @ts-ignore
import { Table } from '@carbon/react';
import { useEffect, useState } from 'react';
import appVersionInfo from '../helpers/appVersionInfo';
import { ObjectWithStringKeysAndValues } from '../interfaces';
import HttpService from '../services/HttpService';

export default function About() {
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
        .map((key) => {
          const value = versionInfoDict[key];
          return (
            <tr key={key}>
              <td className="version-info-column">
                <strong>{key}</strong>
              </td>
              <td className="version-info-column">{value}</td>
            </tr>
          );
        });
      return (
        <>
          <h2 title="This information is configurable by specifying values in version_info.json in the app at build time">
            {title}
          </h2>
          <Table striped bordered>
            <tbody>{tableRows}</tbody>
          </Table>
        </>
      );
    }
    return null;
  };

  return (
    <div>
      <h1>About</h1>
      {versionInfoFromDict('Frontend version information', frontendVersionInfo)}
      {versionInfoFromDict('Backend version information', backendVersionInfo)}
    </div>
  );
}
