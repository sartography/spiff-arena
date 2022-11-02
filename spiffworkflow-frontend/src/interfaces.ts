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
}

export interface ProcessModel {
  id: string;
  process_group_id: string;
  display_name: string;
  primary_file_name: string;
}

// tuple of display value and URL
export type BreadcrumbItem = [displayValue: string, url?: string];

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
