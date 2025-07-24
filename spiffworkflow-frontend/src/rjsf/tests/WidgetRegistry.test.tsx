import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

import { widgetRegistry } from '../registry/WidgetRegistry';
import { WidgetRegistration, CustomWidgetProps } from '../interfaces/CustomWidgetInterfaces';

describe('Widget Registry', () => {
  // Create a simple test widget
  const TestWidget = (props: CustomWidgetProps) => {
    return <div data-testid="test-widget">{props.label}</div>;
  };

  // Clear registry before and after tests
  beforeEach(() => {
    // Clear any existing widgets
    const widgets = widgetRegistry.getAllWidgets();
    Object.keys(widgets).forEach(name => {
      widgetRegistry.unregisterWidget(name);
    });
  });

  afterEach(() => {
    // Clear any widgets created during tests
    const widgets = widgetRegistry.getAllWidgets();
    Object.keys(widgets).forEach(name => {
      widgetRegistry.unregisterWidget(name);
    });
  });

  test('should register and retrieve a widget', () => {
    // Register a test widget
    const registration: WidgetRegistration = {
      name: 'test-widget',
      component: TestWidget,
      metadata: {
        displayName: 'Test Widget',
        description: 'A widget for testing',
        version: '1.0.0',
        author: 'Test Author',
      },
      source: 'core',
    };

    widgetRegistry.registerWidget(registration);

    // Check if widget is registered
    expect(widgetRegistry.hasWidget('test-widget')).toBeTruthy();

    // Get the registered widget
    const widget = widgetRegistry.getWidget('test-widget');
    expect(widget).toBeDefined();

    // Render the widget and check output
    if (widget) {
      render(<widget id="test" value="" onChange={() => {}} label="Test Label" required={false} disabled={false} readonly={false} onBlur={() => {}} onFocus={() => {}} options={{}} formContext={{}} />);
      expect(screen.getByTestId('test-widget')).toHaveTextContent('Test Label');
    }
  });

  test('should return undefined for non-existent widgets', () => {
    expect(widgetRegistry.hasWidget('non-existent')).toBeFalsy();
    expect(widgetRegistry.getWidget('non-existent')).toBeUndefined();
  });

  test('should unregister widgets', () => {
    // Register a test widget
    const registration: WidgetRegistration = {
      name: 'test-widget-to-remove',
      component: TestWidget,
      metadata: {
        displayName: 'Test Widget',
        description: 'A widget for testing',
        version: '1.0.0',
        author: 'Test Author',
      },
      source: 'core',
    };

    widgetRegistry.registerWidget(registration);
    expect(widgetRegistry.hasWidget('test-widget-to-remove')).toBeTruthy();

    // Unregister the widget
    widgetRegistry.unregisterWidget('test-widget-to-remove');
    expect(widgetRegistry.hasWidget('test-widget-to-remove')).toBeFalsy();
  });

  test('should clear extension widgets', () => {
    // Register core widget
    widgetRegistry.registerWidget({
      name: 'core-widget',
      component: TestWidget,
      metadata: {
        displayName: 'Core Widget',
        description: 'A core widget',
        version: '1.0.0',
        author: 'Core Author',
      },
      source: 'core',
    });

    // Register extension widgets
    widgetRegistry.registerWidget({
      name: 'ext1-widget',
      component: TestWidget,
      metadata: {
        displayName: 'Ext1 Widget',
        description: 'An extension widget',
        version: '1.0.0',
        author: 'Ext Author',
      },
      source: 'extension',
      extensionId: 'ext1',
    });

    widgetRegistry.registerWidget({
      name: 'ext2-widget',
      component: TestWidget,
      metadata: {
        displayName: 'Ext2 Widget',
        description: 'Another extension widget',
        version: '1.0.0',
        author: 'Ext Author',
      },
      source: 'extension',
      extensionId: 'ext2',
    });

    // Clear only ext1 extension widgets
    widgetRegistry.clearExtensionWidgets('ext1');
    expect(widgetRegistry.hasWidget('core-widget')).toBeTruthy();
    expect(widgetRegistry.hasWidget('ext1-widget')).toBeFalsy();
    expect(widgetRegistry.hasWidget('ext2-widget')).toBeTruthy();

    // Clear all extension widgets
    widgetRegistry.clearExtensionWidgets();
    expect(widgetRegistry.hasWidget('core-widget')).toBeTruthy();
    expect(widgetRegistry.hasWidget('ext1-widget')).toBeFalsy();
    expect(widgetRegistry.hasWidget('ext2-widget')).toBeFalsy();
  });
});