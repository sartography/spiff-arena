import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import {
  ExtensionUiSchema,
  ProcessFile,
  ProcessModel,
  UiSchemaPageDefinition,
} from '../interfaces';
import HttpService from '../services/HttpService';

export default function Extension() {
  const { targetUris } = useUriListForPermissions();
  const params = useParams();

  const [processModel, setProcessModel] = useState<ProcessModel | null>(null);
  const [UiSchemaPageDefinition, setUiSchemaPageDefinition] =
    useState<UiSchemaPageDefinition | null>(null);

  useEffect(() => {
    const processExtensionResult = (pm: ProcessModel) => {
      setProcessModel(pm);
      const extensionUiSchemaFile = pm.files.find(
        (file: ProcessFile) => file.name === 'extension_uischema.json'
      );
      if (extensionUiSchemaFile && extensionUiSchemaFile.file_contents) {
        const extensionUiSchema: ExtensionUiSchema = JSON.parse(
          extensionUiSchemaFile.file_contents
        );
        const routeIdentifier = `/${params.extension_identifier}`;
        setUiSchemaPageDefinition(extensionUiSchema.routes[routeIdentifier]);
      }
    };

    HttpService.makeCallToBackend({
      path: targetUris.extensionPath,
      successCallback: processExtensionResult,
    });
  }, [targetUris.extensionPath, params]);

  return <main />;
}
