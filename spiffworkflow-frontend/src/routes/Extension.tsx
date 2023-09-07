import { useEffect, useState } from 'react';
import MDEditor from '@uiw/react-md-editor';
import { useParams } from 'react-router-dom';
import { Editor } from '@monaco-editor/react';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { ProcessFile, ProcessModel } from '../interfaces';
import HttpService from '../services/HttpService';
import useAPIError from '../hooks/UseApiError';
import { recursivelyChangeNullAndUndefined } from '../helpers';
import CustomForm from '../components/CustomForm';
import { BACKEND_BASE_URL } from '../config';
import {
  ExtensionPostBody,
  ExtensionUiSchema,
  UiSchemaPageDefinition,
} from '../extension_ui_schema_interfaces';

// eslint-disable-next-line sonarjs/cognitive-complexity
export default function Extension() {
  const { targetUris } = useUriListForPermissions();
  const params = useParams();

  const [_processModel, setProcessModel] = useState<ProcessModel | null>(null);
  const [formData, setFormData] = useState<any>(null);
  const [formButtonsDisabled, setFormButtonsDisabled] = useState(false);
  const [processedTaskData, setProcessedTaskData] = useState<any>(null);
  const [markdownToRenderOnSubmit, setMarkdownToRenderOnSubmit] = useState<
    string | null
  >(null);
  const [markdownToRenderOnLoad, setMarkdownToRenderOnLoad] = useState<
    string | null
  >(null);
  const [filesByName] = useState<{
    [key: string]: ProcessFile;
  }>({});
  const [uiSchemaPageDefinition, setUiSchemaPageDefinition] =
    useState<UiSchemaPageDefinition | null>(null);

  const { addError, removeError } = useAPIError();

  useEffect(() => {
    const processLoadResult = (result: any) => {
      setFormData(result.task_data);
      if (result.rendered_results_markdown) {
        setMarkdownToRenderOnLoad(result.rendered_results_markdown);
      }
    };

    const setConfigsIfDesiredSchemaFile = (
      extensionUiSchemaFile: ProcessFile | null,
      pm: ProcessModel
    ) => {
      if (
        extensionUiSchemaFile &&
        (extensionUiSchemaFile as ProcessFile).file_contents
      ) {
        const extensionUiSchema: ExtensionUiSchema = JSON.parse(
          (extensionUiSchemaFile as any).file_contents
        );

        const pageIdentifier = `/${params.page_identifier}`;
        if (
          extensionUiSchema.pages &&
          Object.keys(extensionUiSchema.pages).includes(pageIdentifier)
        ) {
          const pageDefinition = extensionUiSchema.pages[pageIdentifier];
          setUiSchemaPageDefinition(pageDefinition);
          setProcessModel(pm);

          const postBody: ExtensionPostBody = { extension_input: {} };
          postBody.ui_schema_action = pageDefinition.on_load;
          if (pageDefinition.on_load) {
            HttpService.makeCallToBackend({
              path: `${targetUris.extensionListPath}/${pageDefinition.on_load.api_path}`,
              successCallback: processLoadResult,
              httpMethod: 'POST',
              postBody,
            });
          }
        }
      }
    };
    const processExtensionResult = (processModels: ProcessModel[]) => {
      processModels.forEach((pm: ProcessModel) => {
        let extensionUiSchemaFile: ProcessFile | null = null;
        pm.files.forEach((file: ProcessFile) => {
          filesByName[file.name] = file;
          if (file.name === 'extension_uischema.json') {
            extensionUiSchemaFile = file;
          }
        });
        setConfigsIfDesiredSchemaFile(extensionUiSchemaFile, pm);
      });
    };

    HttpService.makeCallToBackend({
      path: targetUris.extensionListPath,
      successCallback: processExtensionResult,
    });
  }, [
    targetUris.extensionListPath,
    targetUris.extensionPath,
    params,
    filesByName,
  ]);

  const processSubmitResult = (result: any) => {
    setProcessedTaskData(result.task_data);
    if (result.rendered_results_markdown) {
      setMarkdownToRenderOnSubmit(result.rendered_results_markdown);
    }
    setFormButtonsDisabled(false);
  };

  const handleFormSubmit = (formObject: any, _event: any) => {
    if (formButtonsDisabled) {
      return;
    }

    const dataToSubmit = formObject?.formData;

    setFormButtonsDisabled(true);
    setProcessedTaskData(null);
    removeError();
    delete dataToSubmit.isManualTask;

    if (
      uiSchemaPageDefinition &&
      uiSchemaPageDefinition.navigate_to_on_form_submit
    ) {
      let isValid = true;
      const optionString =
        uiSchemaPageDefinition.navigate_to_on_form_submit.replace(
          /{(\w+)}/g,
          (_, k) => {
            const value = dataToSubmit[k];
            if (value === undefined) {
              isValid = false;
              addError({
                message: `Could not find a value for ${k} in form data.`,
              });
            }
            return value;
          }
        );
      if (!isValid) {
        return;
      }
      const url = `${BACKEND_BASE_URL}/extensions-get-data/${params.page_identifier}/${optionString}`;
      window.location.href = url;
      setFormButtonsDisabled(false);
    } else {
      const postBody: ExtensionPostBody = { extension_input: dataToSubmit };
      let apiPath = targetUris.extensionPath;
      if (uiSchemaPageDefinition && uiSchemaPageDefinition.on_form_submit) {
        apiPath = `${targetUris.extensionListPath}/${uiSchemaPageDefinition.on_form_submit.api_path}`;
        postBody.ui_schema_action = uiSchemaPageDefinition.on_form_submit;
      }

      // NOTE: rjsf sets blanks values to undefined and JSON.stringify removes keys with undefined values
      // so we convert undefined values to null recursively so that we can unset values in form fields
      recursivelyChangeNullAndUndefined(dataToSubmit, null);

      HttpService.makeCallToBackend({
        path: apiPath,
        successCallback: processSubmitResult,
        failureCallback: (error: any) => {
          addError(error);
          setFormButtonsDisabled(false);
        },
        httpMethod: 'POST',
        postBody,
      });
    }
  };

  if (uiSchemaPageDefinition) {
    const componentsToDisplay = [<h1>{uiSchemaPageDefinition.header}</h1>];
    const markdownContentsToRender = [];

    if (uiSchemaPageDefinition.markdown_instruction_filename) {
      const markdownFile =
        filesByName[uiSchemaPageDefinition.markdown_instruction_filename];

      if (markdownFile.file_contents) {
        markdownContentsToRender.push(markdownFile.file_contents);
      }
    }
    if (markdownToRenderOnLoad) {
      markdownContentsToRender.push(markdownToRenderOnLoad);
    }

    if (markdownContentsToRender.length > 0) {
      componentsToDisplay.push(
        <div data-color-mode="light">
          <MDEditor.Markdown
            linkTarget="_blank"
            source={markdownContentsToRender.join('\n')}
          />
        </div>
      );
    }

    if (uiSchemaPageDefinition.form_schema_filename) {
      const formSchemaFile =
        filesByName[uiSchemaPageDefinition.form_schema_filename];
      const formUiSchemaFile =
        filesByName[uiSchemaPageDefinition.form_ui_schema_filename];
      if (formSchemaFile.file_contents && formUiSchemaFile.file_contents) {
        componentsToDisplay.push(
          <CustomForm
            id="form-to-submit"
            formData={formData}
            onChange={(obj: any) => {
              setFormData(obj.formData);
            }}
            disabled={formButtonsDisabled}
            onSubmit={handleFormSubmit}
            schema={JSON.parse(formSchemaFile.file_contents)}
            uiSchema={JSON.parse(formUiSchemaFile.file_contents)}
          />
        );
      }
    }
    if (processedTaskData) {
      if (markdownToRenderOnSubmit) {
        componentsToDisplay.push(
          <div data-color-mode="light" className="with-top-margin">
            <MDEditor.Markdown
              className="onboarding"
              linkTarget="_blank"
              source={markdownToRenderOnSubmit}
            />
          </div>
        );
      } else {
        componentsToDisplay.push(
          <>
            <h2 className="with-top-margin">Result:</h2>
            <Editor
              className="with-top-margin"
              height="30rem"
              width="auto"
              defaultLanguage="json"
              defaultValue={JSON.stringify(processedTaskData, null, 2)}
              options={{
                readOnly: true,
                scrollBeyondLastLine: true,
                minimap: { enabled: true },
              }}
            />
          </>
        );
      }
    }
    return <div className="fixed-width-container">{componentsToDisplay}</div>;
  }
  return null;
}
