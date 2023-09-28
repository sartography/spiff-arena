export enum UiSchemaDisplayLocation {
  header_menu_item = 'header_menu_item',
  user_profile_item = 'user_profile_item',
}

export enum UiSchemaPersistenceLevel {
  full = 'full',
  none = 'none',
}

export interface UiSchemaLocationSpecificConfig {
  highlight_on_tabs?: string[];
}

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

export interface UiSchemaAction {
  api_path: string;

  persistence_level?: UiSchemaPersistenceLevel;
  process_id_to_run?: string;
  results_markdown_filename?: string;
  search_params_to_inject?: string[];

  full_api_path?: boolean;
}

export interface UiSchemaPageDefinition {
  header: string;
  api: string;

  form?: UiSchemaForm;
  markdown_instruction_filename?: string;
  navigate_instead_of_post_to_api?: boolean;
  navigate_to_on_form_submit?: string;
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
}

export interface ExtensionPostBody {
  extension_input: any;
  ui_schema_action?: UiSchemaAction;
}
