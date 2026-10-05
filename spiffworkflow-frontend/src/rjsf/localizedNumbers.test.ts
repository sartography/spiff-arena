import { afterEach, describe, expect, it } from 'vitest';
import i18next from '../i18n';
import {
  currencyAffixFor,
  formatLocalizedNumber,
  parseLocalizedNumber,
  resolveNumberLocale,
} from './localizedNumbers';

const numberSchema = { type: 'number' };

const parsedValue = (
  text: string,
  locale: string,
  schema: any = numberSchema,
  options: any = {},
) => {
  const result = parseLocalizedNumber(text, locale, schema, options);
  return result.status === 'valid' ? result.value : result.status;
};

describe('resolveNumberLocale', () => {
  afterEach(async () => {
    await i18next.changeLanguage('en-US');
  });

  it('uses an explicit locale when provided', async () => {
    await i18next.changeLanguage('de');
    expect(resolveNumberLocale('fr-FR')).toBe('fr-FR');
  });

  it('follows the user language when unset or auto', async () => {
    await i18next.changeLanguage('de');
    expect(resolveNumberLocale()).toBe('de');
    expect(resolveNumberLocale('auto')).toBe('de');
  });

  it('follows a user language that has no Arena translation', async () => {
    await i18next.changeLanguage('nl-NL');
    expect(i18next.resolvedLanguage).not.toBe('nl-NL');
    expect(resolveNumberLocale()).toBe('nl-NL');
  });

  it('skips an invalid explicit locale', async () => {
    await i18next.changeLanguage('de');
    expect(resolveNumberLocale('not a locale')).toBe('de');
  });
});

describe('parseLocalizedNumber', () => {
  it('parses German notation', () => {
    expect(parsedValue('100.000,00', 'de-DE')).toBe(100000);
    expect(parsedValue('1.234,56', 'de-DE')).toBe(1234.56);
    expect(parsedValue('100,5', 'de-DE')).toBe(100.5);
    expect(parsedValue('100000', 'de-DE')).toBe(100000);
    expect(parsedValue('-1.234,5', 'de-DE')).toBe(-1234.5);
  });

  it('parses US notation', () => {
    expect(parsedValue('100,000.00', 'en-US')).toBe(100000);
    expect(parsedValue('100.5', 'en-US')).toBe(100.5);
    expect(parsedValue('-1,234.5', 'en-US')).toBe(-1234.5);
  });

  it('rejects the other notation rather than changing magnitude', () => {
    expect(parsedValue('100.5', 'de-DE')).toBe('invalid');
    expect(parsedValue('100,000.00', 'de-DE')).toBe('invalid');
    expect(parsedValue('100.000,00', 'en-US')).toBe('invalid');
    expect(parsedValue('100,5', 'en-US')).toBe('invalid');
    expect(parsedValue('1,00', 'en-US')).toBe('invalid');
  });

  it('accepts whitespace and apostrophe grouping variants', () => {
    expect(parsedValue('100 000,25', 'fr-FR')).toBe(100000.25);
    expect(parsedValue('100\u202f000,25', 'fr-FR')).toBe(100000.25);
    expect(parsedValue("100'000.25", 'de-CH')).toBe(100000.25);
    expect(parsedValue('100\u2019000.25', 'de-CH')).toBe(100000.25);
  });

  it('accepts grouping that a locale only uses optionally', () => {
    expect(parsedValue('1234', 'es')).toBe(1234);
    expect(parsedValue('1.234', 'es')).toBe(1234);
    expect(parsedValue('12,34,567', 'en-IN')).toBe(1234567);
  });

  it('accepts the Unicode minus sign', () => {
    expect(parsedValue('\u22121\u00a0234,5', 'fi')).toBe(-1234.5);
  });

  it('enforces decimals, integer, and negative constraints', () => {
    expect(parsedValue('1,234', 'de-DE', numberSchema, { decimals: 2 })).toBe(
      'invalid',
    );
    expect(parsedValue('1,23', 'de-DE', numberSchema, { decimals: 2 })).toBe(
      1.23,
    );
    expect(parsedValue('12,5', 'de-DE', { type: 'integer' })).toBe('invalid');
    expect(parsedValue('-5', 'de-DE', { type: 'number', minimum: 0 })).toBe(
      'invalid',
    );
    expect(
      parsedValue(
        '-5',
        'de-DE',
        { type: 'number', minimum: 0 },
        {
          allowNegative: true,
        },
      ),
    ).toBe(-5);
  });

  it('treats empty, incomplete, and malformed text distinctly', () => {
    expect(parsedValue('', 'de-DE')).toBe('empty');
    expect(parsedValue('   ', 'de-DE')).toBe('empty');
    expect(parsedValue('-', 'de-DE')).toBe('invalid');
    expect(parsedValue('1e5', 'en-US')).toBe('invalid');
    expect(parsedValue('12a', 'en-US')).toBe('invalid');
    expect(parsedValue('1,2,3', 'de-DE')).toBe('invalid');
  });

  it('accepts a trailing or leading decimal separator', () => {
    expect(parsedValue('100,', 'de-DE')).toBe(100);
    expect(parsedValue(',5', 'de-DE')).toBe(0.5);
  });

  it('returns canonical strings for string schemas', () => {
    expect(parsedValue('1.234,50', 'de-DE', { type: 'string' })).toBe(
      '1234.50',
    );
    expect(parsedValue('-0,00', 'de-DE', { type: 'string' })).toBe('0.00');
  });
});

describe('formatLocalizedNumber', () => {
  it('formats stored numbers and canonical strings', () => {
    expect(formatLocalizedNumber(100000, 'de-DE')).toBe('100.000');
    expect(formatLocalizedNumber(100000, 'de-DE', { decimals: 2 })).toBe(
      '100.000,00',
    );
    expect(formatLocalizedNumber('1234.5', 'en-US', { decimals: 2 })).toBe(
      '1,234.50',
    );
    expect(formatLocalizedNumber(-1234.5, 'de-DE')).toBe('-1.234,5');
    expect(formatLocalizedNumber(1e21, 'en-US')).toBe(
      '1,000,000,000,000,000,000,000',
    );
  });

  it('round-trips through parsing', () => {
    ['de-DE', 'en-US', 'fr-FR', 'de-CH'].forEach((locale) => {
      const text = formatLocalizedNumber(-1234567.89, locale);
      expect(parsedValue(text, locale)).toBe(-1234567.89);
    });
  });

  it('shows non-canonical stored text unchanged', () => {
    expect(formatLocalizedNumber('12,5', 'de-DE')).toBe('12,5');
    expect(formatLocalizedNumber(undefined, 'de-DE')).toBe('');
    expect(formatLocalizedNumber(null, 'de-DE')).toBe('');
  });
});

describe('currencyAffixFor', () => {
  it('places the currency symbol according to the locale', () => {
    expect(currencyAffixFor('EUR', 'de-DE')).toEqual({
      position: 'end',
      symbol: '€',
    });
    expect(currencyAffixFor('USD', 'en-US')).toEqual({
      position: 'start',
      symbol: '$',
    });
  });

  it('falls back to the code for an invalid currency', () => {
    expect(currencyAffixFor('not-a-currency', 'de-DE')).toEqual({
      position: 'end',
      symbol: 'not-a-currency',
    });
    expect(currencyAffixFor(undefined, 'de-DE')).toBeNull();
  });
});
