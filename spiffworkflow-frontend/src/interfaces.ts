export interface Secret {
  id: number;
  key: string;
  value: string;
  creator_user_id: string;
}

export interface RecentProcessModel {
  processGroupIdentifier: string;
  processModelIdentifier: string;
  processModelDisplayName: string;
}

export interface ProcessGroup {
  id: string;
  display_name: string;
  description?: string | null;
}

export interface ProcessFileReference {
  id: string; // The unique id of the process or decision table.
  name: string; // The process or decision table name.
  type: string; // either "decision" or "process"
}

export interface ProcessFile {
  content_type: string;
  last_modified: string;
  name: string;
  process_group_id: string;
  process_model_id: string;
  references: ProcessFileReference[];
  size: number;
  type: string;
}

export interface ProcessModel {
  id: string;
  description: string;
  process_group_id: string;
  display_name: string;
  primary_file_name: string;
  files: ProcessFile[];
}

// tuple of display value and URL
export type HotCrumbItem = [displayValue: string, url?: string];

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
