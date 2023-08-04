export interface User {
  id: number;
  username: string;
}

export interface Secret {
  id: number;
  key: string;
  value: string;
  creator_user_id: string;
}

export interface Onboarding {
  type?: string;
  value?: string;
  process_instance_id?: string;
  task_id?: string;
  instructions: string;
}

export interface ProcessData {
  process_data_identifier: string;
  process_data_value: any;
}

export interface RecentProcessModel {
  processGroupIdentifier?: string;
  processModelIdentifier: string;
  processModelDisplayName: string;
}

export interface TaskPropertiesJson {
  parent: string;
  last_state_change: number;
}

export interface EventDefinition {
  typename: string;
  payload: any;
  event_definitions: [EventDefinition];

  message_var?: string;
}

export interface TaskDefinitionPropertiesJson {
  spec: string;
  event_definition: EventDefinition;
}

export interface SignalButton {
  label: string;
  event: EventDefinition;
}

// Task withouth task data and form info - just the basics
export interface BasicTask {
  id: number;
  guid: string;
  process_instance_id: number;
  bpmn_identifier: string;
  bpmn_name?: string;
  bpmn_process_direct_parent_guid: string;
  bpmn_process_definition_identifier: string;
  state: string;
  typename: string;
  properties_json: TaskPropertiesJson;
  task_definition_properties_json: TaskDefinitionPropertiesJson;

  process_model_display_name: string;
  process_model_identifier: string;
  name_for_display: string;
  can_complete: boolean;
}

// TODO: merge with ProcessInstanceTask
// Currently used like TaskModel in backend
export interface Task extends BasicTask {
  data: any;
  form_schema: any;
  form_ui_schema: any;
  signal_buttons: SignalButton[];

  event_definition?: EventDefinition;
  saved_form_data?: any;
}

// Currently used like ApiTask in backend
export interface ProcessInstanceTask {
  id: string;
  task_id: string;
  can_complete: boolean;
  created_at_in_seconds: number;
  current_user_is_potential_owner: number;
  data: any;
  form_schema: any;
  form_ui_schema: any;
  lane_assignment_id: string;
  name: string;
  process_identifier: string;
  process_initiator_username: string;
  process_instance_id: number;
  process_instance_status: string;
  process_model_display_name: string;
  process_model_identifier: string;
  properties: any;
  state: string;
  task_title: string;
  title: string;
  type: string;
  updated_at_in_seconds: number;

  potential_owner_usernames?: string;
  assigned_user_group_identifier?: string;
  error_message?: string;
}

export interface ProcessReference {
  name: string; // The process or decision Display name.
  identifier: string; // The unique id of the process
  display_name: string;
  process_group_id: string;
  process_model_id: string;
  type: string; // either "decision" or "process"
  file_name: string;
  has_lanes: boolean;
  is_executable: boolean;
  is_primary: boolean;
}

export type ObjectWithStringKeysAndValues = { [key: string]: string };

export interface FilterOperator {
  id: string;
  requires_value: boolean;
}

export interface FilterOperatorMapping {
  [key: string]: FilterOperator;
}

export interface ProcessFile {
  content_type: string;
  last_modified: string;
  name: string;
  process_model_id: string;
  references: ProcessReference[];
  size: number;
  type: string;
  file_contents?: string;
  file_contents_hash?: string;
  bpmn_process_ids?: string[];
}

export interface ProcessInstanceMetadata {
  id: number;
  key: string;
  value: string;
}

export interface ProcessInstance {
  id: number;
  process_model_identifier: string;
  process_model_display_name: string;
  status: string;
  start_in_seconds: number | null;
  end_in_seconds: number | null;
  process_initiator_username: string;
  bpmn_xml_file_contents?: string;
  created_at_in_seconds: number;
  updated_at_in_seconds: number;
  bpmn_version_control_identifier: string;
  bpmn_version_control_type: string;
  process_metadata?: ProcessInstanceMetadata[];
  process_model_with_diagram_identifier?: string;

  // from tasks
  potential_owner_usernames?: string;
  task_id?: string;
  task_updated_at_in_seconds?: number;
  waiting_for?: string;
}

export interface MessageCorrelationProperties {
  [key: string]: string;
}

export interface MessageCorrelations {
  [key: string]: MessageCorrelationProperties;
}

export interface MessageInstance {
  id: number;
  process_model_identifier: string;
  process_model_display_name: string;
  process_instance_id: number;
  name: string;
  message_type: string;
  failure_cause: string;
  status: string;
  created_at_in_seconds: number;
  message_correlations?: MessageCorrelations;
  correlation_keys: any;
}

export interface ReportFilter {
  field_name: string;
  // using any here so we can use this as a string and boolean
  field_value: any;
  operator?: string;
}

export interface ReportColumn {
  Header: string;
  accessor: string;
  filterable: boolean;
}

export interface ReportColumnForEditing extends ReportColumn {
  filter_field_value: string;
  filter_operator: string;
}

export interface ReportMetadata {
  columns: ReportColumn[];
  filter_by: ReportFilter[];
  order_by: string[];
}

export interface ProcessInstanceReport {
  id: number;
  identifier: string;
  name: string;
  report_metadata: ReportMetadata;
}

export interface ProcessGroupLite {
  id: string;
  display_name: string;
}

export interface MetadataExtractionPath {
  key: string;
  path: string;
}

export interface ProcessModel {
  id: string;
  description: string;
  display_name: string;
  primary_file_name: string;
  primary_process_id: string;
  files: ProcessFile[];
  parent_groups?: ProcessGroupLite[];
  metadata_extraction_paths?: MetadataExtractionPath[];
  fault_or_suspend_on_exception?: string;
  exception_notification_addresses?: string[];
  bpmn_version_control_identifier?: string;
}

export interface ProcessGroup {
  id: string;
  display_name: string;
  description?: string | null;
  process_models?: ProcessModel[];
  process_groups?: ProcessGroup[];
  parent_groups?: ProcessGroupLite[];
}

export interface HotCrumbItemObject {
  entityToExplode: ProcessModel | ProcessGroup | string;
  entityType: string;
  linkLastItem?: boolean;
}

export type HotCrumbItemArray = [displayValue: string, url?: string];

// tuple of display value and URL
export type HotCrumbItem = HotCrumbItemArray | HotCrumbItemObject;

export interface ErrorForDisplay {
  message: string;

  error_code?: string;
  error_line?: string;
  file_name?: string;
  line_number?: number;
  messageClassName?: string;
  sentry_link?: string;
  stacktrace?: string[];
  task_id?: string;
  task_name?: string;
  task_trace?: string[];
}

export interface AuthenticationParam {
  id: string;
  type: string;
  required: boolean;
}

export interface AuthenticationItem {
  id: string;
  parameters: AuthenticationParam[];
}

export interface PaginationObject {
  count: number;
  total: number;
  pages: number;
}

export interface CarbonComboBoxSelection {
  selectedItem: any;
}

export interface CarbonComboBoxProcessSelection {
  selectedItem: ProcessReference;
}

export interface PermissionsToCheck {
  [key: string]: string[];
}
export interface PermissionVerbResults {
  [key: string]: boolean;
}
export interface PermissionCheckResult {
  [key: string]: PermissionVerbResults;
}
export interface PermissionCheckResponseBody {
  results: PermissionCheckResult;
}

export interface FormField {
  id: string;
  title: string;
  required?: boolean;
  type: string;
  enum?: string[];
  default?: any;
  pattern?: string;
}

export interface JsonSchemaForm {
  file_contents: string;
  name: string;
  process_model_id: string;
  required: string[];
}

export interface ProcessInstanceEventErrorDetail {
  id: number;
  message: string;
  stacktrace: string[];
  task_line_contents?: string;
  task_line_number?: number;
  task_offset?: number;
  task_trace?: string[];
}

export interface ProcessInstanceLogEntry {
  bpmn_process_definition_identifier: string;
  bpmn_process_definition_name: string;
  bpmn_task_type: string;
  event_type: string;
  spiff_task_guid: string;
  task_definition_identifier: string;
  task_guid: string;
  timestamp: number;
  id: number;
  process_instance_id: number;

  task_definition_name?: string;
  user_id?: number;
  username?: string;
}

export interface ProcessModelCaller {
  display_name: string;
  process_model_id: string;
}

export interface UserGroup {}

type InterstitialPageResponseType =
  | 'task_update'
  | 'error'
  | 'unrunnable_instance';

export interface InterstitialPageResponse {
  type: InterstitialPageResponseType;
  error?: any;
  task?: ProcessInstanceTask;
  process_instance?: ProcessInstance;
}

export interface TestCaseErrorDetails {
  error_messages: string[];
  stacktrace?: string[];
  task_bpmn_identifier?: string;
  task_bpmn_name?: string;
  task_line_contents?: string;
  task_line_number?: number;
  task_trace?: string[];
}

export interface TestCaseResult {
  bpmn_file: string;
  passed: boolean;
  test_case_identifier: string;
  test_case_error_details?: TestCaseErrorDetails;
}

export interface TestCaseResults {
  all_passed: boolean;
  failing: TestCaseResult[];
  passing: TestCaseResult[];
}

export interface DataStoreRecords {
  results: any[];
  pagination: PaginationObject;
}

export interface DataStore {
  name: string;
  type: string;
}

export interface UiSchemaNavItem {
  label: string;
  route: string;
}
export interface UiSchemaPageDefinition {
  header: string;
  api: string;

  form_schema_filename?: any;
  form_ui_schema_filename?: any;
  markdown_instruction_filename?: string;
}
export interface UiSchemaRoute {
  [key: string]: UiSchemaPageDefinition;
}
export interface ExtensionUiSchema {
  navigation_items?: UiSchemaNavItem[];
  routes: UiSchemaRoute;
}
