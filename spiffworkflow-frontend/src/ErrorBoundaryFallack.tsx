import { Button, Content } from '@carbon/react';
import { Routes, Route } from 'react-router-dom';
import React, { useEffect, useState } from 'react';
import { ErrorBoundary, useErrorBoundary } from 'react-error-boundary';
import NavigationBar from './components/NavigationBar';

import HomePageRoutes from './routes/HomePageRoutes';
import About from './routes/About';
import AdminRoutes from './routes/AdminRoutes';

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
import { Notification } from './components/Notification';

type ErrorProps = {
  error: Error;
};

export function ErrorBoundaryFallback({ error }: ErrorProps) {
  // This is displayed if the ErrorBoundary catches an error when rendering the form.
  const { resetBoundary } = useErrorBoundary();

  return (
    <Notification
      title="Something Went Wrong. "
      onClose={() => resetBoundary()}
      type="error"
    >
      <p>
        We encountered an unexpected error. Please try again. If the problem
        persists, please contact your administrator.
      </p>
      <p>{error.message}</p>
      <Button onClick={resetBoundary}>Try again</Button>
    </Notification>
  );
}

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
        <ErrorBoundary fallback={<h1>Something went wrong.</h1>}>
          <Routes>
            <Route path="/*" element={<HomePageRoutes />} />
            <Route path="/about" element={<About />} />
            <Route path="/tasks/*" element={<HomePageRoutes />} />
            <Route
              path="/admin/*"
              element={
                <AdminRoutes extensionUxElements={extensionUxElements} />
              }
            />
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
