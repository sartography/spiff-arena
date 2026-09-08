import { describe, it, expect, beforeAll } from 'vitest';
import i18next from './i18n';

/**
 * Guards WCAG 2.1 AA success criterion 3.1.1 (Language of Page).
 *
 * index.html ships a static lang="en". Because the app switches locales at
 * runtime, the document element has to follow along, or screen readers keep
 * announcing translated content with an English voice.
 */
describe('document language', () => {
  beforeAll(async () => {
    await i18next.changeLanguage('en-US');
  });

  it('reflects the active locale once i18n has initialized', () => {
    expect(document.documentElement.lang).toBe('en-US');
  });

  it('follows the user switching locales', async () => {
    await i18next.changeLanguage('de');
    expect(document.documentElement.lang).toBe('de');

    await i18next.changeLanguage('zh-CN');
    expect(document.documentElement.lang).toBe('zh-CN');
  });

  it('uses a valid BCP-47 tag for every bundled locale', async () => {
    const bcp47 = /^[a-z]{2,3}(-[A-Z][a-z]{3})?(-([A-Z]{2}|\d{3}))?$/;
    const locales = Object.keys(i18next.store.data);

    expect(locales.length).toBeGreaterThan(1);
    for (const locale of locales) {
      await i18next.changeLanguage(locale);
      expect(document.documentElement.lang).toMatch(bcp47);
    }
  });
});
