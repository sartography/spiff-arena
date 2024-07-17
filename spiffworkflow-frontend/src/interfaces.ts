import { ReactElement } from 'react';

export interface User {
  id: number;
  username: string;
}

export interface ApiAction {
  path: string;
  method: string;
}
export interface ApiActions {
  [key: string]: ApiAction;
}

export interface Secret {
  id: number;
  key: string;
  creator_user_id: string;
  value?: string;
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

  authorized?: boolean;
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

  start_in_seconds: number;
  end_in_seconds: number;
  extensions?: any;

  process_model_uses_queued_execution?: boolean;
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
  runtime_info?: any;
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
  name: string; // bpmn_identifier
  process_identifier: string;
  process_initiator_username: string;
  process_instance_id: number;
  process_instance_status: string;
  process_model_display_name: string;
  process_model_identifier: string;
  properties: any;
  state: string;
  title: string; // bpmn_name
  type: string;
  updated_at_in_seconds: number;

  potential_owner_usernames?: string;
  assigned_user_group_identifier?: string;
  error_message?: string;

  // these are actually from HumanTaskModel on the backend
  task_title?: string;
  task_name?: string;
  completed?: boolean;

  // gets shoved onto HumanTaskModel in result
  completed_by_username?: string;
}

export interface ProcessReference {
  identifier: string; // The unique id of the process
  display_name: string;
  relative_location: string;
  type: string; // either "decision" or "process"
  file_name: string;
  properties: any;
}

export type ObjectWithStringKeysAndValues = { [key: string]: string };

export interface FilterOperator {
  id: string;
  requires_value: boolean;
}

export interface FilterOperatorMapping {
  [key: string]: FilterOperator;
}

export interface FilterDisplayTypeMapping {
  [key: string]: string;
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
  bpmn_xml_file_contents_retrieval_error?: string;
  created_at_in_seconds: number;
  updated_at_in_seconds: number;
  bpmn_version_control_identifier: string;
  bpmn_version_control_type: string;
  process_metadata?: ProcessInstanceMetadata[];
  process_model_with_diagram_identifier?: string;
  last_milestone_bpmn_name?: string;
  actions?: ApiActions;

  // from tasks
  potential_owner_usernames?: string;
  task_id?: string;
  task_updated_at_in_seconds?: number;
  waiting_for?: string;

  // from api instance
  process_model_uses_queued_execution?: boolean;
}

export interface CorrelationProperty {
  retrieval_expression: string;
}

export interface CorrelationProperties {
  [key: string]: CorrelationProperty;
}

export interface MessageDefinition {
  correlation_properties: CorrelationProperties;
  schema: any;
}

export interface Messages {
  [key: string]: MessageDefinition;
}

type ReferenceCacheType = 'decision' | 'process' | 'data_store' | 'message';

export interface ReferenceCache {
  identifier: string;
  display_name: string;
  relative_location: string;
  type: ReferenceCacheType;
  file_name: string;
  properties: any;
}

export interface MessageInstance {
  correlation_keys: any;
  counterpart_id: number;
  created_at_in_seconds: number;
  failure_cause: string;
  id: number;
  message_type: string;
  name: string;
  process_instance_id: number;
  process_model_display_name: string;
  process_model_identifier: string;
  status: string;
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
  display_type?: string;
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
  is_executable?: boolean;
  actions?: ApiActions;
}

export interface ProcessGroup {
  id: string;
  display_name: string;
  description?: string | null;
  process_models?: ProcessModel[];
  process_groups?: ProcessGroup[];
  parent_groups?: ProcessGroupLite[];
  messages?: Messages;
}

export interface HotCrumbItemObject {
  entityToExplode: ProcessModel | ProcessGroup | string;
  entityType: string;
  linkLastItem?: boolean;
  checkPermission?: boolean;
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

  task_type?: string;
  output_data?: any;
  expected_data?: any;
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

  task_bpmn_type?: string;
  output_data?: any;
  expected_data?: any;
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
  id: string;
  schema: string;
  description?: string | null;
  location?: string | null;
}

export interface DataStoreType {
  type: string;
  name: string;
  description: string;
}

export interface JsonSchemaExample {
  schema: any;
  ui: any;
  data: any;
}

export interface AuthenticationOption {
  identifier: string;
  label: string;
  uri: string;
}

export interface TaskInstructionForEndUser {
  task_guid: string;
  process_instance_id: number;
  instruction: string;
}

export interface ProcessInstanceProgressResponse {
  error_details?: ProcessInstanceEventErrorDetail;
  instructions: TaskInstructionForEndUser[];
  process_instance?: ProcessInstance;
  process_instance_event?: ProcessInstanceLogEntry;
  task?: ProcessInstanceTask;
}

export interface KeyboardShortcut {
  function: Function;
  label: string;
}

export interface KeyboardShortcuts {
  [key: string]: KeyboardShortcut;
}

export interface SpiffTab {
  path: string;
  display_name: string;
  tooltip?: string;
}

export interface SpiffTableHeader {
  tooltip_text?: string;
  text: string;
}

export interface ElementForArray {
  key: string;
  component: ReactElement | null;
}

export interface PublicTaskForm {
  form_schema: any;
  form_ui_schema: any;
  instructions_for_end_user?: string;
}
export interface PublicTask {
  form: PublicTaskForm;
  task_guid: string;
  process_instance_id: number;
  confirmation_message_markdown: string;
}

export interface RJSFFormObject {
  formData: any;
}

export interface MigrationEvent {
  id: number;
  initial_bpmn_process_hash: string;
  initial_git_revision: string;
  target_bpmn_process_hash: string;
  target_git_revision: string;
  timestamp: string;
  username: string;
}
export interface MigrationCheckResult {
  can_migrate: boolean;
  process_instance_id: number;
  current_git_revision: string;
  current_bpmn_process_hash: string;
}
