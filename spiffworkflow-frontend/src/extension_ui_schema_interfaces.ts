/**
 * These are the configurations that can be added to the extension_uischema.json file for an extension.
 * The top-level object should be an ExtensionUiSchema.
 * See below for more details.
 */

import { FunctionComponent } from 'react';

// Current version of the extension uischema.
export type ExtensionUiSchemaVersion = '0.1' | '0.2';

// All locations that can be specified to display the link to use the extensions.
export enum UiSchemaDisplayLocation {
  // Will appear as a tab under the "Configuration" top nav item.
  configuration_tab_item = 'configuration_tab_item',

  // Will appear in the top nav bar
  header_menu_item = 'header_menu_item',

  /**
   * The page will be used as a route.
   * This route can then be referenced from another ux element or can override other routes.
   */
  routes = 'routes',

  // Will appear in the user profile drop - top right menu with the logout button.
  user_profile_item = 'user_profile_item',
}

/**
 * Determines whether or not a process instance is saved to the database when this extension runs.
 * By default this will be "none" but it can be set to "full" for debugging.
 */
export enum UiSchemaPersistenceLevel {
  full = 'full',
  none = 'none',
}

/**
 * Supported components that can be used on pages.
 * These can be found under "src/components" with more details about how to use.
 * The arguments that can be passed in will generally match the "OwnProps" type defined within each file.
 */
export enum UiSchemaPageComponentList {
  CreateNewInstance = 'CreateNewInstance',
  CustomForm = 'CustomForm',
  MarkdownRenderer = 'MarkdownRenderer',
  ProcessInstanceListTable = 'ProcessInstanceListTable',
  ProcessInstanceRun = 'ProcessInstanceRun',
  SpiffTabs = 'SpiffTabs',
}

// Configs that are specific to certain display locations
export interface UiSchemaLocationSpecificConfig {
  /**
   * Currently only supported on the "configuration_tab_item" location.
   * Specifies which pages should cause the tab item to become highlighted.
   */
  highlight_on_tabs?: string[];
}

// Primary ux element - decribes how the extension should be displayed and accessed from the web ui.
export interface UiSchemaUxElement {
  label: string;
  page: string;
  display_location: UiSchemaDisplayLocation;
  location_specific_configs?: UiSchemaLocationSpecificConfig;
  tooltip?: string;
}

export interface UiSchemaForm {
  form_schema_filename: any;
  form_ui_schema_filename: any;

  form_submit_button_label?: string;
}

// The action that should be taken when something happens such as a form submit.
export interface UiSchemaAction {
  /**
   * The api_path to call.
   * This will normally just be the colon delimited process model identifier for the extension minus the extension process group.
   * For example: extensions/path/to/extension -> path:to:extension
   * This will interpolate patterns like "{task_data_var}" if found in the task data.
   */
  api_path: string;

  /**
   * By default, when submitting an action it makes the call to the extension endpoint in backend.
   * This tells the web ui to use the api_path as the full path and removes the extension portion.
   */
  is_full_api_path?: boolean;

  persistence_level?: UiSchemaPersistenceLevel;

  /**
   * The bpmn process id of the bpmn diagram.
   * If there are multiple bpmn files within the process model, this can be used to specify which process to run.
   * If there is only one bpmn file or if only the primary file is used, then this is not needed.
   */
  process_id_to_run?: string;

  /**
   * Markdown file to display the results with.
   * This file can use jinja and can reference task data created from the process similar markdown used from within a process model.
   */
  results_markdown_filename?: string;

  /**
   * By default the extension data comes a key called "task_data" in the api result.
   * This will instead allow the extension data to be set by the full result.
   * this is useful when making api calls to non-extension apis.
   */
  set_extension_data_from_full_api_result?: string;

  /**
   * Parameters to grab from the search params of the url.
   * This is useful when linking from one extension to another so params can be grabbed and given to the process model when running.
   */
  search_params_to_inject?: string[];

  /**
   * The variable name in the task data that will define the components to use.
   * This is useful if the components for the page need to be generated more dynamically.
   * This variable should be defined from the on_load process.
   */
  ui_schema_page_components_variable?: string;
}

// Component to use for the page
export interface UiSchemaPageComponent {
  // The name must match a value in "UiSchemaPageComponentList".
  name: keyof typeof UiSchemaPageComponentList;

  /**
   * Arguments given to the component.
   * Details above under "UiSchemaPageComponentList".
   *
   * If an argument is a string prepended by SPIFF_PROCESS_MODEL_FILE if will look for a file defined in that process model.
   * FROM_JSON can be used with SPIFF_PROCESS_MODEL_FILE to tell frontend to load the contents with JSON.parse
   * Example: "SPIFF_PROCESS_MODEL_FILE:FROM_JSON:::filename.json"
   * Example: "SPIFF_PROCESS_MODEL_FILE:::filename.md"
   */
  arguments: object;

  /**
   * Instead of posting the extension api, this makes it set the "href" to the api_path.
   * This is useful if the intent is download a file.
   */
  navigate_instead_of_post_to_api?: boolean;

  /**
   * Path to navigate to after submitting the form.
   * This will interpolate patterns like "{task_data_var}" if found in the task data.
   */
  navigate_to_on_form_submit?: string;

  on_form_submit?: UiSchemaAction;
}

// The primary definition for a page.
export interface UiSchemaPageDefinition {
  // Primary header to use for the page.
  header?: string;

  components?: UiSchemaPageComponent[];

  /**
   * Path to navigate to after calling the on_load api.
   * This will interpolate patterns like "{task_data_var}" if found in the task data.
   */
  navigate_to_on_load?: string;

  /**
   * The on_load action to use.
   * Useful for gathering data from a process model when loading the extension.
   */
  on_load?: UiSchemaAction;

  /**
   * Specifies whether or not open links specified in the markdown to open in a new tab or not.
   * NOTE: this gets used for both the markdown_instruction_filename and markdown returned from the on_load.
   * It may be better to move functionality to the action but not 100% sure how.
   */
  open_links_in_new_tab?: boolean;
}

// The name of the page along with its definition.
export interface UiSchemaPage {
  [key: string]: UiSchemaPageDefinition;
}

/**
 * Top-level object in the extension_uischema.json file.
 * Read the interfaces above for more info.
 */
export interface ExtensionUiSchema {
  pages: UiSchemaPage;
  ux_elements?: UiSchemaUxElement[];
  version?: ExtensionUiSchemaVersion;

  // Disable the extension which is useful during development of an extension.
  disabled?: boolean;
}

/** ********************************************
 * These are types given to and received from the api calls.
 * These are not specified from within the extension_uischema.json file.
 */
export interface ExtensionPostBody {
  extension_input: any;
  ui_schema_action?: UiSchemaAction;
}

// The response returned from the backend
export interface ExtensionApiResponse {
  // Task data generated from the process model.
  task_data: any;

  // The markdown string rendered from the process model.
  rendered_results_markdown?: string;
}

export type SupportedComponentList = {
  [key in keyof typeof UiSchemaPageComponentList]: FunctionComponent<any>;
};
/** ************************************* */
