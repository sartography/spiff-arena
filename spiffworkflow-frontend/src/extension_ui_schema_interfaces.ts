export enum ExtensionUiSchemaVersion {
  ONE = '1',
}

// all locations that can be specified to display the link to use the extensions.
export enum UiSchemaDisplayLocation {
  // will appear as a tab under the "Configuration" top nav item.
  configuration_tab_item = 'configuration_tab_item',

  // will appear in the top nav bar
  header_menu_item = 'header_menu_item',

  /**
   * the page will be used as a route.
   * this route can then be referenced from another ux element or can override other routes.
   */
  routes = 'routes',

  // will appear in the user profile drop - top right menu with the logout button.
  user_profile_item = 'user_profile_item',
}

/**
 * determines whether or not a process instance is saved to the database when this extension runs.
 * by default this will be "none" but it can be set to "full" for debugging.
 */
export enum UiSchemaPersistenceLevel {
  full = 'full',
  none = 'none',
}

/**
 *  supported components that can be used on pages.
 *  these can be found under "src/components" with more details about how to use.
 *  the arguments that can be passed in will generally match the "OwnProps" type defined within each file.
 */
export enum UiSchemaPageComponentList {
  CreateNewInstance = 'CreateNewInstance',
  CustomForm = 'CustomForm',
  MarkdownRenderer = 'MarkdownRenderer',
  ProcessInstanceListTable = 'ProcessInstanceListTable',
  ProcessInstanceRun = 'ProcessInstanceRun',
  SpiffTabs = 'SpiffTabs',
}

// configs that are specific to certain display locations
export interface UiSchemaLocationSpecificConfig {
  /**
   * currently only supported on the "configuration_tab_item" location.
   * specifies which pages should cause the tab item to become highlighted.
   */
  highlight_on_tabs?: string[];
}

// primary ux element - decribes how the extension should be displayed and accessed from the web ui.
export interface UiSchemaUxElement {
  label: string;
  page: string;
  display_location: UiSchemaDisplayLocation;
  location_specific_configs?: UiSchemaLocationSpecificConfig;
}

export interface UiSchemaForm {
  form_schema_filename: any;
  form_ui_schema_filename: any;

  form_submit_button_label?: string;
}

// the action that should be taken when something happens such as a form submit.
export interface UiSchemaAction {
  /**
   * the api_path to call.
   * this will normally just be the colon delimited process model identifier for the extension minus the extension process group.
   * for example: extensions/path/to/extension -> path:to:extension
   */
  api_path: string;

  persistence_level?: UiSchemaPersistenceLevel;

  /**
   * the bpmn process id of the bpmn diagram.
   * if there are multiple bpmn files within the process model, this can be used to specify which process to run.
   * if there is only one bpmn file or if only the primary file is used, then this is not needed.
   */
  process_id_to_run?: string;

  /**
   * markdown file to display the results with.
   * this file can use jinja and can reference task data created from the process similar markdown used from within a process model.
   */
  results_markdown_filename?: string;

  /**
   * parameters to grab from the search params of the url.
   * this is useful when linking from one extension to another so params can be grabbed and given to the process model when running.
   */
  search_params_to_inject?: string[];

  /**
   * by default, when submitting an action it makes the call to the extension endpoint in backend.
   * this tells the web ui to use the api_path as the full path and removes the extension portion.
   * NOTE: this appears unused by any extension.
   */
  full_api_path?: boolean;

  // NOTE: this appears unused by any extension.
  ui_schema_page_components_variable?: string;
}

// component to use for the page
export interface UiSchemaPageComponent {
  // the name must match a value in "UiSchemaPageComponentList".
  name: keyof typeof UiSchemaPageComponentList;

  // arguments given to the component - details above under "UiSchemaPageComponentList".
  arguments: object;

  /**
   * instead of posting the extension api, this makes it set the "href" to the api_path.
   * this is useful if the intent is download a file.
   * NOTE: this appears unused by any extension.
   */
  navigate_instead_of_post_to_api?: boolean;

  /**
   * path to navigate to after submitting the form.
   * this will interpolate patterns like "{task_data_var}" if found in the task data.
   */
  navigate_to_on_form_submit?: string;

  on_form_submit?: UiSchemaAction;
}

export interface UiSchemaPageDefinition {
  header?: string;
  api?: string;

  components?: UiSchemaPageComponent[];
  form?: UiSchemaForm;
  markdown_instruction_filename?: string;
  navigate_instead_of_post_to_api?: boolean;
  navigate_to_on_form_submit?: string;
  navigate_to_on_load?: string;
  on_form_submit?: UiSchemaAction;
  on_load?: UiSchemaAction;
  open_links_in_new_tab?: boolean;
}

export interface UiSchemaPage {
  [key: string]: UiSchemaPageDefinition;
}

export interface ExtensionUiSchema {
  pages: UiSchemaPage;
  disabled?: boolean;
  ux_elements?: UiSchemaUxElement[];
  version?: ExtensionUiSchemaVersion;
}

export interface ExtensionPostBody {
  extension_input: any;
  ui_schema_action?: UiSchemaAction;
}

export interface ExtensionApiResponse {
  task_data: any;

  rendered_results_markdown?: string;
  ui_schema_page_components?: UiSchemaPageComponent[];
}
