import React from 'react';
import { initializeWidgetDiscovery } from './WidgetDiscovery';
import { widgetRegistry } from './WidgetRegistry';
import DateRangePickerWidget from '../custom_widgets/DateRangePicker/DateRangePickerWidget';
import MarkDownFieldWidget from '../custom_widgets/MarkDownFieldWidget/MarkDownFieldWidget';
import TypeaheadWidget from '../custom_widgets/TypeaheadWidget/TypeaheadWidget';
// import RatingWidgetNew from '../custom_widgets/NewWidget';

/**
 * Register core widgets with the registry
 */
function registerCoreWidgets(): void {
  // Register built-in widgets
  widgetRegistry.registerWidget({
    name: 'date-range',
    component: DateRangePickerWidget,
    source: 'core',
  });

  widgetRegistry.registerWidget({
    name: 'markdown',
    component: MarkDownFieldWidget,
    source: 'core',
  });

  // widgetRegistry.registerWidget({
  //   name: 'newwidget',
  //   component: RatingWidgetNew,
  //   source: 'core',
  // });

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
