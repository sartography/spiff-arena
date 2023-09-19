import { Content } from '@carbon/react';
import { Routes, Route } from 'react-router-dom';
import React, { useEffect, useState } from 'react';
import { ErrorBoundary } from 'react-error-boundary';
import NavigationBar from './components/NavigationBar';

import About from './routes/About';

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

export default function ContainerForExtensions() {
  const [extensionUxElements, setExtensionNavigationItems] = useState<
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
    permissionRequestData
  );

  // eslint-disable-next-line sonarjs/cognitive-complexity
  useEffect(() => {
    if (!permissionsLoaded) {
      return;
    }

    const processExtensionResult = (processModels: ProcessModel[]) => {
      const eni: UiSchemaUxElement[] = processModels
        .map((processModel: ProcessModel) => {
          const extensionUiSchemaFile = processModel.files.find(
            (file: ProcessFile) => file.name === 'extension_uischema.json'
          );
          if (extensionUiSchemaFile && extensionUiSchemaFile.file_contents) {
            try {
              const extensionUiSchema: ExtensionUiSchema = JSON.parse(
                extensionUiSchemaFile.file_contents
              );
              if (extensionUiSchema.ux_elements) {
                return extensionUiSchema.ux_elements;
              }
            } catch (jsonParseError: any) {
              console.error(
                `Unable to get navigation items for ${processModel.id}`
              );
            }
          }
          return [] as UiSchemaUxElement[];
        })
        .flat();
      if (eni) {
        setExtensionNavigationItems(eni);
      }
    };

    if (ability.can('GET', targetUris.extensionListPath)) {
      HttpService.makeCallToBackend({
        path: targetUris.extensionListPath,
        successCallback: processExtensionResult,
      });
    }
  }, [targetUris.extensionListPath, permissionsLoaded, ability]);

  return (
    <>
      <NavigationBar extensionUxElements={extensionUxElements} />
      <Content className={contentClassName}>
        <ScrollToTop />
        <ErrorBoundary FallbackComponent={ErrorBoundaryFallback}>
          <Routes>
            <Route
              path="/*"
              element={<BaseRoutes extensionUxElements={extensionUxElements} />}
            />
            <Route path="/about" element={<About />} />
            <Route path="/editor/*" element={<EditorRoutes />} />
            <Route
              path="/extensions/:page_identifier"
              element={<Extension />}
            />
          </Routes>
        </ErrorBoundary>
      </Content>
    </>
  );
}
