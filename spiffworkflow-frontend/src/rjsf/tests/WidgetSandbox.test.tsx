import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

import { evaluateWidgetCode, SandboxedWidget } from '../sandbox/WidgetSandbox';

// Mock DOMPurify to avoid actual sanitation during tests
jest.mock('dompurify', () => ({
  sanitize: jest.fn((code) => code),
}));

describe('Widget Sandbox', () => {
  test('should evaluate safe widget code', async () => {
    const safeCode = `
      module.exports = {
        default: function SafeWidget(props) {
          const React = require('react');
          return React.createElement('div', { 
            'data-testid': 'safe-widget' 
          }, props.label);
        }
      };
    `;

    const component = await evaluateWidgetCode(safeCode);
    expect(component).not.toBeNull();

    if (component) {
      render(
        <component
          id="test"
          label="Safe Widget"
          value=""
          onChange={() => {}}
          required={false}
          disabled={false}
          readonly={false}
          onBlur={() => {}}
          onFocus={() => {}}
          options={{}}
          formContext={{}}
        />
      );

      expect(screen.getByTestId('safe-widget')).toHaveTextContent('Safe Widget');
    }
  });

  test('should reject code accessing document', async () => {
    const unsafeCode = `
      module.exports = {
        default: function UnsafeWidget(props) {
          const React = require('react');
          // Try to access document
          document.cookie = "test=1";
          return React.createElement('div', null, props.label);
        }
      };
    `;

    const component = await evaluateWidgetCode(unsafeCode);
    expect(component).toBeNull();
  });

  test('should reject code accessing window', async () => {
    const unsafeCode = `
      module.exports = {
        default: function UnsafeWidget(props) {
          const React = require('react');
          // Try to access window
          window.location = "https://example.com";
          return React.createElement('div', null, props.label);
        }
      };
    `;

    const component = await evaluateWidgetCode(unsafeCode);
    expect(component).toBeNull();
  });

  test('should reject code using eval', async () => {
    const unsafeCode = `
      module.exports = {
        default: function UnsafeWidget(props) {
          const React = require('react');
          // Try to use eval
          eval("alert('hello')");
          return React.createElement('div', null, props.label);
        }
      };
    `;

    const component = await evaluateWidgetCode(unsafeCode);
    expect(component).toBeNull();
  });

  test('should render SandboxedWidget with error handling', async () => {
    // This will be evaluated and rendered in SandboxedWidget
    const validCode = `
      module.exports = {
        default: function ValidWidget(props) {
          const React = require('react');
          return React.createElement('div', { 
            'data-testid': 'sandboxed-widget' 
          }, props.label);
        }
      };
    `;

    render(
      <SandboxedWidget
        widgetSource={validCode}
        id="test"
        label="Sandboxed Widget"
        value=""
        onChange={() => {}}
        required={false}
        disabled={false}
        readonly={false}
        onBlur={() => {}}
        onFocus={() => {}}
        options={{}}
        formContext={{}}
      />
    );

    // Initially shows loading
    expect(screen.getByText('Loading widget...')).toBeInTheDocument();

    // Wait for widget to load and render
    const widgetElement = await screen.findByTestId('sandboxed-widget');
    expect(widgetElement).toHaveTextContent('Sandboxed Widget');
  });

  test('should handle errors in widget rendering', async () => {
    // Widget with runtime error
    const errorCode = `
      module.exports = {
        default: function ErrorWidget(props) {
          const React = require('react');
          // This will cause a runtime error
          throw new Error('Widget error');
          return React.createElement('div', null, props.label);
        }
      };
    `;

    render(
      <SandboxedWidget
        widgetSource={errorCode}
        id="test"
        label="Error Widget"
        value=""
        onChange={() => {}}
        required={false}
        disabled={false}
        readonly={false}
        onBlur={() => {}}
        onFocus={() => {}}
        options={{}}
        formContext={{}}
      />
    );

    // Wait for error message
    const errorElement = await screen.findByText(/Widget error/);
    expect(errorElement).toBeInTheDocument();
  });
});