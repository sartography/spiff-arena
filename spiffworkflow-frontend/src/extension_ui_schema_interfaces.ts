export enum UiSchemaDisplayLocation {
  header_menu_item = 'header_menu_item',
  user_profile_item = 'user_profile_item',
}

export enum UiSchemaPersistenceLevel {
  full = 'full',
  none = 'none',
}

export interface UiSchemaUxElement {
  label: string;
  page: string;
  display_location: UiSchemaDisplayLocation;
}

export interface UiSchemaAction {
  api_path: string;

  persistence_level?: UiSchemaPersistenceLevel;
  navigate_to_on_form_submit?: string;
  results_markdown_filename?: string;
}

export interface UiSchemaPageDefinition {
  header: string;
  api: string;

  on_load?: UiSchemaAction;
  on_form_submit?: UiSchemaAction;
  form_schema_filename?: any;
  form_ui_schema_filename?: any;
  markdown_instruction_filename?: string;
  navigate_to_on_form_submit?: string;
}

export interface UiSchemaPage {
  [key: string]: UiSchemaPageDefinition;
}

export interface ExtensionUiSchema {
  ux_elements?: UiSchemaUxElement[];
  pages: UiSchemaPage;
}

export interface ExtensionPostBody {
  extension_input: any;
  ui_schema_action?: UiSchemaAction;
}
