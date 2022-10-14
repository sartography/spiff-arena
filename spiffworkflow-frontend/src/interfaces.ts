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
