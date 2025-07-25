import React from 'react';
import { initializeWidgetDiscovery } from './WidgetDiscovery';
import { widgetRegistry } from './WidgetRegistry';
import DateRangePickerWidget from '../custom_widgets/DateRangePicker/DateRangePickerWidget';
import MarkDownFieldWidget from '../custom_widgets/MarkDownFieldWidget/MarkDownFieldWidget';
import TypeaheadWidget from '../custom_widgets/TypeaheadWidget/TypeaheadWidget';
import { withSandbox } from '../sandbox/WidgetSandbox';

/**
 * Register core widgets with the registry
 */
function registerCoreWidgets(): void {
  // Register built-in widgets
  widgetRegistry.registerWidget({
    name: 'date-range',
    component: DateRangePickerWidget,
    metadata: {
      displayName: 'Date Range Picker',
      description: 'A widget for selecting a range of dates',
      version: '1.0.0',
      author: 'SpiffWorkflow',
      category: 'core',
    },
    source: 'core',
  });

  widgetRegistry.registerWidget({
    name: 'markdown',
    component: MarkDownFieldWidget,
    metadata: {
      displayName: 'Markdown Editor',
      description: 'A widget for editing markdown content',
      version: '1.0.0',
      author: 'SpiffWorkflow',
      category: 'core',
    },
    source: 'core',
  });

  // Use withProps higher-order component like in the original CustomForm
  const customTypeaheadWidget = function TypeaheadWithTheme(props: any) {
    return React.createElement(TypeaheadWidget, {
      ...props,
      reactJsonSchemaFormTheme: 'mui',
    });
  };

  widgetRegistry.registerWidget({
    name: 'typeahead',
    component: customTypeaheadWidget,
    metadata: {
      displayName: 'Typeahead',
      description: 'A widget for typeahead search functionality',
      version: '1.0.0',
      author: 'SpiffWorkflow',
      category: 'core',
    },
    source: 'core',
  });
}

/**
 * Initialize the widget system
 * This function should be called during application startup
 */
export async function initializeWidgets(): Promise<void> {
  // Register core widgets
  registerCoreWidgets();

  // Load extension widgets
  await initializeWidgetDiscovery();

  console.log('Widget system initialized successfully');
}
