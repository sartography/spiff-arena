/**
 * Utilities for JSON Schema file handling in BPMN workflows
 * These are used for User Task form schema files
 */

/**
 * Validation pattern for schema file names
 * Names must:
 * - Start and end with a lowercase letter or number
 * - Contain only lowercase letters, numbers, and hyphens
 * - Be at least 2 characters long
 */
export const SCHEMA_NAME_PATTERN = /^[a-z0-9][0-9a-z-]*[a-z0-9]$/;

/**
 * File extensions for JSON schema related files
 */
export const SCHEMA_EXTENSIONS = {
  SCHEMA: '-schema.json',
  UI_SCHEMA: '-uischema.json',
  EXAMPLE_DATA: '-exampledata.json',
} as const;

/**
 * Extract base name from a schema filename
 * e.g., "my-form-schema.json" -> "my-form"
 * e.g., "my-form-uischema.json" -> "my-form"
 * e.g., "my-form-exampledata.json" -> "my-form"
 */
export function extractSchemaBaseName(fileName: string): string {
  if (!fileName) return '';
  return fileName
    .replace(/-schema\.json$/, '')
    .replace(/-uischema\.json$/, '')
    .replace(/-exampledata\.json$/, '');
}

/**
 * Sanitize a string to create a valid schema name
 * - Converts to lowercase
 * - Replaces non-alphanumeric characters with hyphens
 * - Removes leading/trailing hyphens
 * - Limits length to 50 characters
 */
export function toValidSchemaName(input: string): string {
  if (!input) return '';
  return input
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .substring(0, 50);
}

/**
 * Validate a schema name
 * Returns null if valid, or an error message if invalid
 */
export function validateSchemaName(name: string): string | null {
  if (!name) {
    return 'Name is required';
  }
  if (name.length < 2) {
    return 'Name must be at least 2 characters';
  }
  if (!SCHEMA_NAME_PATTERN.test(name)) {
    return 'Name must start and end with a letter or number, and contain only lowercase letters, numbers, and hyphens';
  }
  return null;
}

/**
 * Generate the three schema file names from a base name
 */
export function getSchemaFileNames(baseName: string): {
  schemaFile: string;
  uiSchemaFile: string;
  exampleDataFile: string;
} {
  return {
    schemaFile: `${baseName}${SCHEMA_EXTENSIONS.SCHEMA}`,
    uiSchemaFile: `${baseName}${SCHEMA_EXTENSIONS.UI_SCHEMA}`,
    exampleDataFile: `${baseName}${SCHEMA_EXTENSIONS.EXAMPLE_DATA}`,
  };
}

/**
 * Check if a filename is a schema-related file
 */
export function isSchemaFile(fileName: string): boolean {
  return (
    fileName.endsWith(SCHEMA_EXTENSIONS.SCHEMA) ||
    fileName.endsWith(SCHEMA_EXTENSIONS.UI_SCHEMA) ||
    fileName.endsWith(SCHEMA_EXTENSIONS.EXAMPLE_DATA)
  );
}

/**
 * Derive a default schema name from a BPMN element
 * Uses the element's name or ID, sanitized to a valid schema name
 */
export function deriveSchemaNameFromElement(element: any): string {
  if (!element) return 'new-form';

  const businessObject = element.businessObject || element;
  const name = businessObject.name || businessObject.id || '';

  const derived = toValidSchemaName(name);
  return derived || 'new-form';
}
