import { useEffect, useState } from 'react';
import MDEditor from '@uiw/react-md-editor';
import { useParams } from 'react-router-dom';
import validator from '@rjsf/validator-ajv8';
import { Form } from '../rjsf/carbon_theme';
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

  const [_processModel, setProcessModel] = useState<ProcessModel | null>(null);
  const [formData, setFormData] = useState<any>(null);
  const [filesByName] = useState<{
    [key: string]: ProcessFile;
  }>({});
  const [uiSchemaPageDefinition, setUiSchemaPageDefinition] =
    useState<UiSchemaPageDefinition | null>(null);

  useEffect(() => {
    const processExtensionResult = (pm: ProcessModel) => {
      setProcessModel(pm);
      let extensionUiSchemaFile: ProcessFile | null = null;
      pm.files.forEach((file: ProcessFile) => {
        filesByName[file.name] = file;
        if (file.name === 'extension_uischema.json') {
          extensionUiSchemaFile = file;
        }
      });

      // typescript is really confused by extensionUiSchemaFile so force it since we are properly checking
      if (
        extensionUiSchemaFile &&
        (extensionUiSchemaFile as ProcessFile).file_contents
      ) {
        const extensionUiSchema: ExtensionUiSchema = JSON.parse(
          (extensionUiSchemaFile as any).file_contents
        );
        const routeIdentifier = `/${params.extension_identifier}`;
        setUiSchemaPageDefinition(extensionUiSchema.routes[routeIdentifier]);
      }
    };

    HttpService.makeCallToBackend({
      path: targetUris.extensionPath,
      successCallback: processExtensionResult,
    });
  }, [targetUris.extensionPath, params, filesByName]);

  const handleFormSubmit = (formObject: any, _event: any) => {
    console.log('formObject', formObject);
  };

  if (uiSchemaPageDefinition) {
    const componentsToDisplay = [<h1>{uiSchemaPageDefinition.header}</h1>];

    if (uiSchemaPageDefinition.markdown_instruction_filename) {
      const markdownFile =
        filesByName[uiSchemaPageDefinition.markdown_instruction_filename];

      if (markdownFile.file_contents) {
        componentsToDisplay.push(
          <div data-color-mode="light">
            <MDEditor.Markdown
              linkTarget="_blank"
              source={markdownFile.file_contents}
            />
          </div>
        );
      }
    }

    if (uiSchemaPageDefinition.form_schema_filename) {
      const formSchemaFile =
        filesByName[uiSchemaPageDefinition.form_schema_filename];
      const formUiSchemaFile =
        filesByName[uiSchemaPageDefinition.form_ui_schema_filename];
      if (formSchemaFile.file_contents && formUiSchemaFile.file_contents) {
        componentsToDisplay.push(
          <Form
            id="form-to-submit"
            formData={formData}
            onChange={(obj: any) => {
              setFormData(obj.formData);
            }}
            onSubmit={handleFormSubmit}
            schema={JSON.parse(formSchemaFile.file_contents)}
            uiSchema={JSON.parse(formUiSchemaFile.file_contents)}
            validator={validator}
            omitExtraData
          />
        );
      }
    }
    // eslint-disable-next-line react/jsx-no-useless-fragment
    return <>{componentsToDisplay}</>;
  }
  return null;
}
