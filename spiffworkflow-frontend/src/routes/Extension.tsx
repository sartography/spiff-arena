import { useCallback, useEffect, useState } from 'react';
import { Button } from '@carbon/react';
import { useParams, useSearchParams } from 'react-router-dom';
import { Editor } from '@monaco-editor/react';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import {
  ObjectWithStringKeysAndFunctionValues,
  ProcessFile,
  ProcessModel,
} from '../interfaces';
import HttpService from '../services/HttpService';
import useAPIError from '../hooks/UseApiError';
import { recursivelyChangeNullAndUndefined, makeid } from '../helpers';
import CustomForm from '../components/CustomForm';
import { BACKEND_BASE_URL } from '../config';
import {
  ExtensionApiResponse,
  ExtensionPostBody,
  ExtensionUiSchema,
  UiSchemaPageComponent,
  UiSchemaPageDefinition,
} from '../extension_ui_schema_interfaces';
import ErrorDisplay from '../components/ErrorDisplay';
import FormattingService from '../services/FormattingService';
import ProcessInstanceRun from '../components/ProcessInstanceRun';
import MarkdownRenderer from '../components/MarkdownRenderer';
import LoginHandler from '../components/LoginHandler';
import SpiffTabs from '../components/SpiffTabs';
import ProcessInstanceListTable from '../components/ProcessInstanceListTable';
import CreateNewInstance from './CreateNewInstance';

type OwnProps = {
  pageIdentifier?: string;
  displayErrors?: boolean;
};

// eslint-disable-next-line sonarjs/cognitive-complexity
export default function Extension({
  pageIdentifier,
  displayErrors = true,
}: OwnProps) {
  const { targetUris } = useUriListForPermissions();
  const params = useParams();
  const [searchParams] = useSearchParams();

  const [processModel, setProcessModel] = useState<ProcessModel | null>(null);
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
  const [readyForComponentsToDisplay, setReadyForComponentsToDisplay] =
    useState<boolean>(false);
  const [uiSchemaPageComponents, setuiSchemaPageComponents] = useState<
    UiSchemaPageComponent[] | null
  >(null);

  const { addError, removeError } = useAPIError();

  const supportedComponents: ObjectWithStringKeysAndFunctionValues = {
    CreateNewInstance,
    CustomForm,
    MarkdownRenderer,
    ProcessInstanceListTable,
    ProcessInstanceRun,
    SpiffTabs,
  };

  const interpolateNavigationString = useCallback(
    (navigationString: string, baseData: any) => {
      let isValid = true;
      const data = { backend_base_url: BACKEND_BASE_URL, ...baseData };
      const optionString = navigationString.replace(/{(\w+)}/g, (_, k) => {
        const value = data[k];
        if (value === undefined) {
          isValid = false;
          addError({
            message: `Could not find a value for ${k} in form data.`,
          });
        }
        return value;
      });
      if (!isValid) {
        return null;
      }
      return optionString;
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );
  const processLoadResult = useCallback(
    (result: ExtensionApiResponse, pageDefinition: UiSchemaPageDefinition) => {
      setFormData(result.task_data);
      if (pageDefinition.navigate_to_on_load) {
        const optionString = interpolateNavigationString(
          pageDefinition.navigate_to_on_load,
          result.task_data
        );
        if (optionString !== null) {
          window.location.href = optionString;
        }
      }
      if (result.rendered_results_markdown) {
        const newMarkdown = FormattingService.checkForSpiffFormats(
          result.rendered_results_markdown
        );
        setMarkdownToRenderOnLoad(newMarkdown);
      }
      if (
        pageDefinition.on_load &&
        pageDefinition.on_load.ui_schema_page_components_variable
      ) {
        setuiSchemaPageComponents(
          result.task_data[
            pageDefinition.on_load.ui_schema_page_components_variable
          ]
        );
      }
      setReadyForComponentsToDisplay(true);
    },
    [interpolateNavigationString]
  );

  const setConfigsIfDesiredSchemaFile = useCallback(
    // eslint-disable-next-line sonarjs/cognitive-complexity
    (extensionUiSchemaFile: ProcessFile | null, pm: ProcessModel) => {
      if (
        extensionUiSchemaFile &&
        (extensionUiSchemaFile as ProcessFile).file_contents
      ) {
        const extensionUiSchema: ExtensionUiSchema = JSON.parse(
          (extensionUiSchemaFile as any).file_contents
        );

        let pageIdentifierToUse = pageIdentifier;
        if (!pageIdentifierToUse) {
          pageIdentifierToUse = `/${params.page_identifier}`;
        }
        if (
          extensionUiSchema.pages &&
          Object.keys(extensionUiSchema.pages).includes(pageIdentifierToUse)
        ) {
          const pageDefinition = extensionUiSchema.pages[pageIdentifierToUse];
          setUiSchemaPageDefinition(pageDefinition);
          setuiSchemaPageComponents(pageDefinition.components || null);
          setProcessModel(pm);
          pm.files.forEach((file: ProcessFile) => {
            filesByName[file.name] = file;
          });

          if (pageDefinition.on_load) {
            const postBody: ExtensionPostBody = { extension_input: {} };
            if (pageDefinition.on_load.search_params_to_inject) {
              pageDefinition.on_load.search_params_to_inject.forEach(
                (searchParam: string) => {
                  if (searchParams.get(searchParam) !== undefined) {
                    postBody.extension_input[searchParam] =
                      searchParams.get(searchParam);
                  }
                }
              );
            }
            postBody.ui_schema_action = pageDefinition.on_load;
            HttpService.makeCallToBackend({
              path: `${targetUris.extensionListPath}/${pageDefinition.on_load.api_path}`,
              successCallback: (result: ExtensionApiResponse) =>
                processLoadResult(result, pageDefinition),
              httpMethod: 'POST',
              postBody,
            });
          } else {
            setReadyForComponentsToDisplay(true);
          }
        }
      }
    },
    [
      targetUris.extensionListPath,
      params.page_identifier,
      searchParams,
      filesByName,
      processLoadResult,
      pageIdentifier,
    ]
  );

  useEffect(() => {
    const processExtensionResult = (processModels: ProcessModel[]) => {
      processModels.forEach((pm: ProcessModel) => {
        let extensionUiSchemaFile: ProcessFile | null = null;
        pm.files.forEach((file: ProcessFile) => {
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
    setConfigsIfDesiredSchemaFile,
    targetUris.extensionListPath,
    targetUris.extensionPath,
  ]);

  const processSubmitResult = (
    pageDefinitionToUse: UiSchemaPageDefinition | UiSchemaPageComponent,
    result: ExtensionApiResponse
  ) => {
    console.log('pageDefinitionToUse', pageDefinitionToUse);
    if (pageDefinitionToUse && pageDefinitionToUse.navigate_to_on_form_submit) {
      const optionString = interpolateNavigationString(
        pageDefinitionToUse.navigate_to_on_form_submit,
        result.task_data
      );
      if (optionString !== null) {
        window.location.href = optionString;
      }
    } else {
      setProcessedTaskData(result.task_data);
      if (result.rendered_results_markdown) {
        const newMarkdown = FormattingService.checkForSpiffFormats(
          result.rendered_results_markdown
        );
        setMarkdownToRenderOnSubmit(newMarkdown);
      }
      setFormButtonsDisabled(false);
    }
  };

  // eslint-disable-next-line sonarjs/cognitive-complexity
  const handleFormSubmit = (
    pageDefinitionToUse: UiSchemaPageDefinition | UiSchemaPageComponent,
    formObject: any,
    event: any
  ) => {
    event.preventDefault();

    if (formButtonsDisabled) {
      return;
    }

    const dataToSubmit = formObject?.formData;

    setFormButtonsDisabled(true);
    setProcessedTaskData(null);
    removeError();
    delete dataToSubmit.isManualTask;

    if (
      pageDefinitionToUse &&
      pageDefinitionToUse.navigate_instead_of_post_to_api
    ) {
      let optionString: string | null = '';
      if (pageDefinitionToUse.navigate_to_on_form_submit) {
        optionString = interpolateNavigationString(
          pageDefinitionToUse.navigate_to_on_form_submit,
          dataToSubmit
        );
        if (optionString !== null) {
          window.location.href = optionString;
          setFormButtonsDisabled(false);
        }
      }
    } else {
      let postBody: ExtensionPostBody = { extension_input: dataToSubmit };
      let apiPath = targetUris.extensionPath;
      if (pageDefinitionToUse && pageDefinitionToUse.on_form_submit) {
        if (pageDefinitionToUse.on_form_submit.is_full_api_path) {
          apiPath = `/${pageDefinitionToUse.on_form_submit.api_path}`;
          postBody = dataToSubmit;
        } else {
          apiPath = `${targetUris.extensionListPath}/${pageDefinitionToUse.on_form_submit.api_path}`;
        }
        postBody.ui_schema_action = pageDefinitionToUse.on_form_submit;
      }

      // NOTE: rjsf sets blanks values to undefined and JSON.stringify removes keys with undefined values
      // so we convert undefined values to null recursively so that we can unset values in form fields
      recursivelyChangeNullAndUndefined(dataToSubmit, null);
      HttpService.makeCallToBackend({
        path: apiPath,
        successCallback: (result: ExtensionApiResponse) =>
          processSubmitResult(pageDefinitionToUse, result),
        failureCallback: (error: any) => {
          addError(error);
          setFormButtonsDisabled(false);
        },
        httpMethod: 'POST',
        postBody,
      });
    }
  };

  const renderComponentArguments = (component: UiSchemaPageComponent) => {
    const argumentsForComponent: any = component.arguments;
    if (processModel) {
      Object.keys(argumentsForComponent).forEach((argName: string) => {
        const argValue = argumentsForComponent[argName];
        if (
          typeof argValue === 'string' &&
          argValue.startsWith('SPIFF_PROCESS_MODEL_FILE:')
        ) {
          const [macro, fileName] = argValue.split(':::');
          const macroList = macro.split(':');
          const pmFileForArg = processModel.files.find(
            (pmFile: ProcessFile) => {
              return pmFile.name === fileName;
            }
          );
          if (pmFileForArg) {
            let newArgValue = pmFileForArg.file_contents;
            if (macroList.includes('FROM_JSON')) {
              newArgValue = JSON.parse(newArgValue || '{}');
            }
            argumentsForComponent[argName] = newArgValue;
          }
        }
      });
    }
    if (component.name === 'CustomForm') {
      argumentsForComponent.onSubmit = (formObject: any, event: any) =>
        handleFormSubmit(component, formObject, event);
      argumentsForComponent.formData = formData;
      argumentsForComponent.id = argumentsForComponent.id || makeid(20);
      argumentsForComponent.onChange = (obj: any) => {
        setFormData(obj.formData);
      };
    }
    return argumentsForComponent;
  };

  if (readyForComponentsToDisplay && uiSchemaPageDefinition) {
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

    let mdEditorLinkTarget: string | undefined = '_blank';
    if (uiSchemaPageDefinition.open_links_in_new_tab === false) {
      mdEditorLinkTarget = undefined;
    }

    if (markdownContentsToRender.length > 0) {
      componentsToDisplay.push(
        <MarkdownRenderer
          linkTarget={mdEditorLinkTarget}
          source={markdownContentsToRender.join('\n')}
          wrapperClassName="with-bottom-margin"
        />
      );
    }

    if (uiSchemaPageComponents) {
      uiSchemaPageComponents.forEach((component: UiSchemaPageComponent) => {
        const componentName = component.name;
        if (supportedComponents[componentName]) {
          const argumentsForComponent = renderComponentArguments(component);
          componentsToDisplay.push(
            supportedComponents[componentName](argumentsForComponent)
          );
        } else {
          console.error(
            `Extension tried to use component with name '${component.name}' but that is not allowed.`
          );
        }
      });
    }

    const uiSchemaForm = uiSchemaPageDefinition.form;
    if (uiSchemaForm) {
      const formSchemaFile = filesByName[uiSchemaForm.form_schema_filename];
      const formUiSchemaFile =
        filesByName[uiSchemaForm.form_ui_schema_filename];
      const submitButtonText =
        uiSchemaForm.form_submit_button_label || 'Submit';
      if (formSchemaFile.file_contents && formUiSchemaFile.file_contents) {
        componentsToDisplay.push(
          <CustomForm
            id="form-to-submit"
            formData={formData}
            onChange={(obj: any) => {
              setFormData(obj.formData);
            }}
            disabled={formButtonsDisabled}
            onSubmit={(formObject: any, event: any) =>
              handleFormSubmit(uiSchemaPageDefinition, formObject, event)
            }
            schema={JSON.parse(formSchemaFile.file_contents)}
            uiSchema={JSON.parse(formUiSchemaFile.file_contents)}
          >
            <Button
              type="submit"
              id="submit-button"
              disabled={formButtonsDisabled}
            >
              {submitButtonText}
            </Button>
          </CustomForm>
        );
      }
    }
    if (processedTaskData) {
      if (markdownToRenderOnSubmit) {
        componentsToDisplay.push(
          <MarkdownRenderer
            className="onboarding"
            linkTarget="_blank"
            source={markdownToRenderOnSubmit}
            wrapperClassName="with-top-margin"
          />
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
    return (
      <div className="fixed-width-container">
        {displayErrors ? <ErrorDisplay /> : null}
        {componentsToDisplay}
      </div>
    );
  }

  // load the login handler if the components haven't loaded to ensure
  // things aren't loading because the user is not logged in
  return (
    <div className="fixed-width-container">
      <LoginHandler />
    </div>
  );
}
