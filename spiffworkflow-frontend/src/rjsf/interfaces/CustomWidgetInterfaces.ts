import { ComponentType } from 'react';

/**
 * Standard props interface for custom widgets
 * This is based on the React JSON Schema Form widget props
 */
export interface CustomWidgetProps {
  id: string;
  schema: any;
  uiSchema: any;
  value: any;
  required: boolean;
  disabled: boolean;
  readonly: boolean;
  label: string;
  onChange: (value: any) => void;
  onBlur: (id: string, value: any) => void;
  onFocus: (id: string, value: any) => void;
  options: any;
  formContext: any;
  rawErrors?: string[];
  placeholder?: string;
  autofocus?: boolean;
}

/**
 * Interface for widget registration
 * This defines how widgets are registered with our system
 */
export interface WidgetRegistration {
  // The name of the widget to be used in ui:widget
  name: string;

  // The actual widget component
  component: ComponentType<CustomWidgetProps>;

  // Source of the widget (core, extension, user)
  source: 'core' | 'extension' | 'user';

  // Extension ID if it's from an extension
  extensionId?: string;
}

/**
 * Interface for external widget source file
 * This defines how widget code is stored in extension files
 */
export interface ExternalWidgetSource {
  // The content of the widget file (JavaScript/TypeScript code)
  sourceCode: string;

  // Widget registration information
  registration: Omit<WidgetRegistration, 'component'>;

  // Dependencies required by this widget
  dependencies?: Record<string, string>;
}

/**
 * Widget registry interface
 * Defines the methods available on the widget registry
 */
export interface WidgetRegistry {
  // Register a widget with the system
  registerWidget: (registration: WidgetRegistration) => void;

  // Get a widget by name
  getWidget: (name: string) => ComponentType<CustomWidgetProps> | undefined;

  // Get all registered widgets
  getAllWidgets: () => Record<string, WidgetRegistration>;

  // Check if a widget is registered
  hasWidget: (name: string) => boolean;

  // Remove a widget from the registry
  unregisterWidget: (name: string) => void;

  // Clear all extension widgets (used when extensions are reloaded)
  clearExtensionWidgets: (extensionId?: string) => void;
}
