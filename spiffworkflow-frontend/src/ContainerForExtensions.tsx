import { Content } from '@carbon/react';
import { Routes, Route, useLocation } from 'react-router-dom';
import React, { useEffect, useState } from 'react';
import { ErrorBoundary } from 'react-error-boundary';

import ScrollToTop from './components/ScrollToTop';
import EditorRoutes from './routes/EditorRoutes';
import Extension from './routes/Extension';
import { useUriListForPermissions } from './hooks/UriListForPermissions';
import { PermissionsToCheck, ProcessFile, ProcessModel } from './interfaces';
import { usePermissionFetcher } from './hooks/PermissionService';
import {
  ExtensionUiSchema,
  UiSchemaUxElement,
} from './extension_ui_schema_interfaces';
import HttpService from './services/HttpService';
import { ErrorBoundaryFallback } from './ErrorBoundaryFallack';
import BaseRoutes from './routes/BaseRoutes';
import BackendIsDown from './routes/BackendIsDown';
import Login from './routes/Login';
import NavigationBar from './components/NavigationBar';
import useAPIError from './hooks/UseApiError';

export default function ContainerForExtensions() {
  const [backendIsUp, setBackendIsUp] = useState<boolean | null>(null);
  const [extensionUxElements, setExtensionUxElements] = useState<
    UiSchemaUxElement[] | null
  >(null);

  let contentClassName = 'main-site-body-centered';
  if (window.location.pathname.startsWith('/editor/')) {
    contentClassName = 'no-center-stuff';
  }
  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.extensionListPath]: ['GET'],
  };
  const { ability, permissionsLoaded } = usePermissionFetcher(
    permissionRequestData,
  );

  const { removeError } = useAPIError();

  const location = useLocation();

  // never carry an error message across to a different path
  useEffect(() => {
    removeError();
    // if we include the removeError function to the dependency array of this useEffect, it causes
    // an infinite loop where the page with the error adds the error,
    // then this runs and it removes the error, etc. it is ok not to include it here, i think, because it never changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  // eslint-disable-next-line sonarjs/cognitive-complexity
  useEffect(() => {
    const processExtensionResult = (processModels: ProcessModel[]) => {
      const eni: UiSchemaUxElement[] = processModels
        .map((processModel: ProcessModel) => {
          const extensionUiSchemaFile = processModel.files.find(
            (file: ProcessFile) => file.name === 'extension_uischema.json',
          );
          if (extensionUiSchemaFile && extensionUiSchemaFile.file_contents) {
            try {
              const extensionUiSchema: ExtensionUiSchema = JSON.parse(
                extensionUiSchemaFile.file_contents,
              );
              if (
                extensionUiSchema &&
                extensionUiSchema.ux_elements &&
                !extensionUiSchema.disabled
              ) {
                return extensionUiSchema.ux_elements;
              }
            } catch (jsonParseError: any) {
              console.error(
                `Unable to get navigation items for ${processModel.id}`,
              );
            }
          }
          return [] as UiSchemaUxElement[];
        })
        .flat();
      if (eni) {
        setExtensionUxElements(eni);
      }
    };

    const getExtensions = () => {
      setBackendIsUp(true);
      if (!permissionsLoaded) {
        return;
      }
      if (ability.can('GET', targetUris.extensionListPath)) {
        HttpService.makeCallToBackend({
          path: targetUris.extensionListPath,
          successCallback: processExtensionResult,
        });
      } else {
        // set to an empty array so we know that it loaded
        setExtensionUxElements([]);
      }
    };

    HttpService.makeCallToBackend({
      path: targetUris.statusPath,
      successCallback: getExtensions,
      failureCallback: () => setBackendIsUp(false),
    });
  }, [
    targetUris.extensionListPath,
    targetUris.statusPath,
    permissionsLoaded,
    ability,
  ]);

  const routeComponents = () => {
    return (
      <Routes>
        <Route
          path="*"
          element={<BaseRoutes extensionUxElements={extensionUxElements} />}
        />
        <Route path="editor/*" element={<EditorRoutes />} />
        <Route path="extensions/:page_identifier" element={<Extension />} />
        <Route path="login" element={<Login />} />
      </Routes>
    );
  };

  const backendIsDownPage = () => {
    return [<BackendIsDown />];
  };

  const innerComponents = () => {
    if (backendIsUp === null) {
      return [];
    }
    if (backendIsUp) {
      return routeComponents();
    }
    return backendIsDownPage();
  };

  return (
    <>
      <NavigationBar extensionUxElements={extensionUxElements} />
      <Content className={contentClassName}>
        <ScrollToTop />
        <ErrorBoundary FallbackComponent={ErrorBoundaryFallback}>
          {innerComponents()}
        </ErrorBoundary>
      </Content>
    </>
  );
}
