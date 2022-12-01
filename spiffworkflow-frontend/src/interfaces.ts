export interface Secret {
  id: number;
  key: string;
  value: string;
  creator_user_id: string;
}

export interface RecentProcessModel {
  processGroupIdentifier?: string;
  processModelIdentifier: string;
  processModelDisplayName: string;
}

export interface ProcessReference {
  id: string; // The unique id of the process or decision table.
  name: string; // The process or decision Display name.
  identifier: string;
  display_name: string;
  process_group_id: string;
  process_model_id: string;
  type: string; // either "decision" or "process"
  file_name: string;
  has_lanes: boolean;
  is_executable: boolean;
  is_primary: boolean;
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
}

export interface ProcessInstance {
  id: number;
  process_model_identifier: string;
  process_model_display_name: string;
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
  message_identifier: string;
  message_type: string;
  failure_cause: string;
  status: string;
  created_at_in_seconds: number;
  message_correlations?: MessageCorrelations;
}

export interface ProcessInstanceReport {
  id: string;
  display_name: string;
}

export interface ProcessGroupLite {
  id: string;
  display_name: string;
}

export interface ProcessModel {
  id: string;
  description: string;
  display_name: string;
  primary_file_name: string;
  files: ProcessFile[];
  parent_groups?: ProcessGroupLite[];
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
  sentry_link?: string;
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
  selectedItem: ProcessModel;
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
  required: boolean;
  type: string;
  enum: string[];
}

export interface ReportColumn {
  Header: string;
  accessor: string;
  filterable: boolean;
}
