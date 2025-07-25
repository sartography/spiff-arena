import React, { ComponentType, createContext, useContext } from 'react';
import {
  WidgetRegistry as WidgetRegistryInterface,
  WidgetRegistration,
  CustomWidgetProps,
} from '../interfaces/CustomWidgetInterfaces';

/**
 * Implementation of the widget registry
 * This registry keeps track of all registered widgets and provides methods to access them
 */
class WidgetRegistryImpl implements WidgetRegistryInterface {
  // Map of widget name to registration
  private widgets: Record<string, WidgetRegistration> = {};

  /**
   * Register a widget with the system
   * @param registration The widget registration information
   */
  registerWidget(registration: WidgetRegistration): void {
    if (this.widgets[registration.name]) {
      console.warn(
        `Widget '${registration.name}' is already registered. It will be overwritten.`,
      );
    }

    this.widgets[registration.name] = registration;
  }

  /**
   * Get a widget by name
   * @param name The name of the widget
   * @returns The widget component or undefined if not found
   */
  getWidget(name: string): ComponentType<CustomWidgetProps> | undefined {
    const registration = this.widgets[name];
    return registration?.component;
  }

  /**
   * Get all registered widgets
   * @returns A record of all widget registrations
   */
  getAllWidgets(): Record<string, WidgetRegistration> {
    return { ...this.widgets };
  }

  /**
   * Check if a widget is registered
   * @param name The name of the widget
   * @returns True if the widget is registered, false otherwise
   */
  hasWidget(name: string): boolean {
    return !!this.widgets[name];
  }

  /**
   * Remove a widget from the registry
   * @param name The name of the widget to remove
   */
  unregisterWidget(name: string): void {
    if (this.widgets[name]) {
      delete this.widgets[name];
    }
  }

  /**
   * Clear all extension widgets
   * If extensionId is provided, only clear widgets from that extension
   * @param extensionId Optional extension ID to limit which widgets are cleared
   */
  clearExtensionWidgets(extensionId?: string): void {
    if (extensionId) {
      // Remove only widgets from the specified extension
      Object.keys(this.widgets).forEach((name) => {
        if (
          this.widgets[name].source === 'extension' &&
          this.widgets[name].extensionId === extensionId
        ) {
          delete this.widgets[name];
        }
      });
    } else {
      // Remove all extension widgets
      Object.keys(this.widgets).forEach((name) => {
        if (this.widgets[name].source === 'extension') {
          delete this.widgets[name];
        }
      });
    }
  }
}

// Create singleton instance of the registry
export const widgetRegistry = new WidgetRegistryImpl();

// Create React context for the registry
export const WidgetRegistryContext =
  createContext<WidgetRegistryInterface>(widgetRegistry);

/**
 * Hook to access the widget registry in React components
 * @returns The widget registry instance
 */
export function useWidgetRegistry(): WidgetRegistryInterface {
  return useContext(WidgetRegistryContext);
}

/**
 * Provider component to make the registry available in the React tree
 */
export function WidgetRegistryProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  return React.createElement(
    WidgetRegistryContext.Provider,
    { value: widgetRegistry },
    children,
  );
}
