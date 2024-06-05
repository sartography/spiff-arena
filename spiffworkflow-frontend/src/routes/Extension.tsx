import { createElement, useCallback, useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { Editor } from '@monaco-editor/react';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { ProcessFile, ProcessModel } from '../interfaces';
import HttpService from '../services/HttpService';
import useAPIError from '../hooks/UseApiError';
import { recursivelyChangeNullAndUndefined, makeid } from '../helpers';
import CustomForm from '../components/CustomForm';
import { BACKEND_BASE_URL } from '../config';
import {
  ExtensionApiResponse,
  ExtensionPostBody,
  ExtensionUiSchema,
  SupportedComponentList,
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

  const supportedComponents: SupportedComponentList = {
    CreateNewInstance,
    CustomForm,
    MarkdownRenderer,
    ProcessInstanceListTable,
    ProcessInstanceRun,
    SpiffTabs,
  };

  const interpolateNavigationString = useCallback(
    (navigationString: string, baseData: any) => {
      // This will interpolate patterns like "{task_data_var}" if found in the task data.
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
    [],
  );
  const processLoadResult = useCallback(
    (result: ExtensionApiResponse, pageDefinition: UiSchemaPageDefinition) => {
      if (pageDefinition.navigate_to_on_load) {
        const optionString = interpolateNavigationString(
          pageDefinition.navigate_to_on_load,
          result.task_data,
        );
        if (optionString !== null) {
          window.location.href = optionString;
        }
      }
      if (result.rendered_results_markdown) {
        const newMarkdown = FormattingService.checkForSpiffFormats(
          result.rendered_results_markdown,
        );
        setMarkdownToRenderOnLoad(newMarkdown);
      }

      const taskDataCopy = { ...result.task_data };
      if (
        pageDefinition.on_load &&
        pageDefinition.on_load.ui_schema_page_components_variable
      ) {
        setuiSchemaPageComponents(
          result.task_data[
            pageDefinition.on_load.ui_schema_page_components_variable
          ],
        );

        // we were getting any AJV8Validator error when we had this data in the task data
        // when we attempted to submit a form using this task data.
        // The error was:
        //  Uncaught RangeError: Maximum call stack size exceeded
        //
        // Removing the ui schema page components dictionary seems to resolve it.
        delete taskDataCopy[
          pageDefinition.on_load.ui_schema_page_components_variable
        ];
      }
      setFormData(taskDataCopy);
      setReadyForComponentsToDisplay(true);
    },
    [interpolateNavigationString],
  );

  const setConfigsIfDesiredSchemaFile = useCallback(
    // eslint-disable-next-line sonarjs/cognitive-complexity
    (extensionUiSchemaFile: ProcessFile | null, pm: ProcessModel) => {
      if (
        extensionUiSchemaFile &&
        (extensionUiSchemaFile as ProcessFile).file_contents
      ) {
        const extensionUiSchema: ExtensionUiSchema = JSON.parse(
          (extensionUiSchemaFile as any).file_contents,
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
                },
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
    ],
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
  }, [setConfigsIfDesiredSchemaFile, targetUris.extensionListPath]);

  const processSubmitResult = (
    pageComponent: UiSchemaPageComponent,
    result: ExtensionApiResponse,
  ) => {
    let taskData = result.task_data;
    if (pageComponent.on_form_submit?.set_extension_data_from_full_api_result) {
      taskData = result;
    }
    if (pageComponent && pageComponent.navigate_to_on_form_submit) {
      const optionString = interpolateNavigationString(
        pageComponent.navigate_to_on_form_submit,
        taskData,
      );
      if (optionString !== null) {
        window.location.href = optionString;
      }
    } else {
      setProcessedTaskData(taskData);
      if (result.rendered_results_markdown) {
        const newMarkdown = FormattingService.checkForSpiffFormats(
          result.rendered_results_markdown,
        );
        setMarkdownToRenderOnSubmit(newMarkdown);
      }
      setFormButtonsDisabled(false);
    }
  };

  const handleFormSubmit = (
    pageComponent: UiSchemaPageComponent,
    formObject: any,
    event: any,
    // eslint-disable-next-line sonarjs/cognitive-complexity
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

    if (pageComponent && pageComponent.navigate_instead_of_post_to_api) {
      let optionString: string | null = '';
      if (pageComponent.navigate_to_on_form_submit) {
        optionString = interpolateNavigationString(
          pageComponent.navigate_to_on_form_submit,
          dataToSubmit,
        );
        if (optionString !== null) {
          window.location.href = optionString;
          setFormButtonsDisabled(false);
        }
      }
    } else {
      let postBody: ExtensionPostBody = { extension_input: dataToSubmit };
      let apiPathRaw = targetUris.extensionPath;
      if (pageComponent && pageComponent.on_form_submit) {
        apiPathRaw = pageComponent.on_form_submit.api_path.replace(/^\/?/, '/');
        if (!pageComponent.on_form_submit.is_full_api_path) {
          apiPathRaw = `${targetUris.extensionListPath}${apiPathRaw}`;
        } else {
          postBody = dataToSubmit;
        }
        postBody.ui_schema_action = pageComponent.on_form_submit;
      }
      const apiPath =
        interpolateNavigationString(apiPathRaw, dataToSubmit) || apiPathRaw;

      // NOTE: rjsf sets blanks values to undefined and JSON.stringify removes keys with undefined values
      // so we convert undefined values to null recursively so that we can unset values in form fields
      recursivelyChangeNullAndUndefined(dataToSubmit, null);
      HttpService.makeCallToBackend({
        path: apiPath,
        successCallback: (result: ExtensionApiResponse) =>
          processSubmitResult(pageComponent, result),
        failureCallback: (error: any) => {
          addError(error);
          setFormButtonsDisabled(false);
        },
        httpMethod: 'POST',
        postBody,
      });
    }
  };

  // eslint-disable-next-line sonarjs/cognitive-complexity
  const renderComponentArguments = (component: UiSchemaPageComponent) => {
    const argumentsForComponent: any = component.arguments;
    if (processModel && argumentsForComponent) {
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
            },
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
        />,
      );
    }

    if (uiSchemaPageComponents) {
      uiSchemaPageComponents.forEach((component: UiSchemaPageComponent) => {
        const componentName = component.name;
        if (supportedComponents[componentName]) {
          const argumentsForComponent = renderComponentArguments(component);
          componentsToDisplay.push(
            createElement(
              supportedComponents[componentName],
              argumentsForComponent,
            ),
          );
        } else {
          console.error(
            `Extension tried to use component with name '${component.name}' but that is not allowed.`,
          );
        }
      });
    }

    if (processedTaskData) {
      if (markdownToRenderOnSubmit) {
        componentsToDisplay.push(
          <MarkdownRenderer
            className="onboarding"
            linkTarget="_blank"
            source={markdownToRenderOnSubmit}
            wrapperClassName="with-top-margin"
          />,
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
          </>,
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
