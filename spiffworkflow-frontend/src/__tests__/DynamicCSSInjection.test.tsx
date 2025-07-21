import { render, cleanup } from '@testing-library/react';
import DOMPurify from 'dompurify';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import DynamicCSSInjection from '../components/DynamicCSSInjection';

// Mock DOMPurify
vi.mock('dompurify', async () => {
  return {
    default: {
      sanitize: vi.fn((content) => `sanitized:${content}`),
    },
  };
});

describe('DynamicCSSInjection', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    vi.clearAllMocks();
  });

  afterEach(() => {
    // Clean up after each test
    cleanup();

    // Clean up any style elements created by the component
    document.querySelectorAll('[id^="spiff-extension-css-"]').forEach((el) => {
      el.parentNode?.removeChild(el);
    });
  });

  it('sanitizes CSS content before injection', () => {
    const maliciousCSS =
      'body { color: red; } /* */ @import url(evil.css); /* */';
    const testId = 'test-css';

    render(<DynamicCSSInjection cssContent={maliciousCSS} id={testId} />);

    // Check that DOMPurify.sanitize was called with the expected parameters
    expect(DOMPurify.sanitize).toHaveBeenCalledWith(
      maliciousCSS,
      expect.objectContaining({
        FORBID_TAGS: ['style', 'link'],
        USE_PROFILES: { css: true },
      }),
    );

    // Check that a style element was created with the expected ID
    const styleElement = document.getElementById(
      `spiff-extension-css-${testId}`,
    );
    expect(styleElement).not.toBeNull();
    expect(styleElement?.tagName.toLowerCase()).toBe('style');
    expect(styleElement?.getAttribute('type')).toBe('text/css');

    // Check that the sanitized content was used
    expect(styleElement?.textContent).toBe(`sanitized:${maliciousCSS}`);
  });

  it('removes style element on unmount', () => {
    const testId = 'unmount-test';

    const { unmount } = render(
      <DynamicCSSInjection cssContent="test" id={testId} />,
    );

    // Element should exist after render
    const styleElementBefore = document.getElementById(
      `spiff-extension-css-${testId}`,
    );
    expect(styleElementBefore).not.toBeNull();

    // Unmount the component
    unmount();

    // Element should be removed after unmount
    const styleElementAfter = document.getElementById(
      `spiff-extension-css-${testId}`,
    );
    expect(styleElementAfter).toBeNull();
  });
});
