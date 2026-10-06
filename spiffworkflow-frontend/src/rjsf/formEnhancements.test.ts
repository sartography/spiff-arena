import { describe, expect, it } from 'vitest';
import {
  applyCalculatedFields,
  coerceFormattedNumberValue,
  evaluateCalculatedExpression,
  formatNumberForDisplay,
  stripNumberFormatting,
} from './formEnhancements';

const enUS = { locale: 'en-US' };
const deDE = { locale: 'de-DE' };

describe('formatted number helpers', () => {
  it('adds comma separators for large numbers', () => {
    expect(formatNumberForDisplay('1234567.89', enUS)).toBe('1,234,567.89');
    expect(formatNumberForDisplay(1234567.89, enUS)).toBe('1,234,567.89');
  });

  it('formats stored values in the field locale', () => {
    expect(formatNumberForDisplay(100000, { ...deDE, decimals: 2 })).toBe(
      '100.000,00',
    );
  });

  it('submits numeric schema values as numbers', () => {
    expect(
      coerceFormattedNumberValue('1,234,567.89', { type: 'number' }, enUS),
    ).toBe(1234567.89);
    expect(
      coerceFormattedNumberValue('100.000,00', { type: 'number' }, deDE),
    ).toBe(100000);
  });

  it('submits string schema values as unformatted numeric strings', () => {
    expect(coerceFormattedNumberValue('1,234', { type: 'string' }, enUS)).toBe(
      '1234',
    );
    expect(
      coerceFormattedNumberValue('1.234,50', { type: 'string' }, deDE),
    ).toBe('1234.50');
  });

  it('preserves empty values as undefined', () => {
    expect(
      coerceFormattedNumberValue('', { type: 'number' }, enUS),
    ).toBeUndefined();
  });

  it('rejects notation from another locale instead of reinterpreting it', () => {
    expect(
      coerceFormattedNumberValue('100.000,00', { type: 'number' }, enUS),
    ).toEqual({ invalidNumberText: '100.000,00' });
    expect(
      coerceFormattedNumberValue('100,5', { type: 'number' }, enUS),
    ).toEqual({ invalidNumberText: '100,5' });
    expect(
      coerceFormattedNumberValue('100.5', { type: 'number' }, deDE),
    ).toEqual({ invalidNumberText: '100.5' });
    expect(
      coerceFormattedNumberValue('1.50', { type: 'string' }, deDE),
    ).toEqual({ invalidNumberText: '1.50' });
  });

  it('rounds stored values to the configured decimals for display', () => {
    const options = { ...deDE, decimals: 2 };
    expect(formatNumberForDisplay(1.1 * 3, options)).toBe('3,30');
    expect(formatNumberForDisplay(12.345, options)).toBe('12,35');
    expect(formatNumberForDisplay(-0.004, options)).toBe('0,00');
    expect(formatNumberForDisplay(999.995, options)).toBe('1.000,00');
    expect(formatNumberForDisplay(2.5, { ...deDE, decimals: 0 })).toBe('3');
  });

  it('honors non-negative schemas when normalizing calculation input', () => {
    expect(
      stripNumberFormatting('-1,234', { type: 'number', minimum: 0 }),
    ).toBe('1234');
  });

  it('rejects negative input for non-negative schemas', () => {
    expect(
      coerceFormattedNumberValue(
        '-1,234',
        { type: 'number', minimum: 0 },
        enUS,
      ),
    ).toEqual({ invalidNumberText: '-1,234' });
  });

  it('keeps invalid fractional input visible for integer schemas and rejects it', () => {
    expect(formatNumberForDisplay('12.9', enUS)).toBe('12.9');
    expect(
      coerceFormattedNumberValue('12.9', { type: 'integer' }, enUS),
    ).toEqual({ invalidNumberText: '12.9' });
  });
});

describe('calculated field helpers', () => {
  it('evaluates arithmetic expressions against local form data', () => {
    expect(
      evaluateCalculatedExpression('days_0_90 + days_91_180 * 2', {
        days_0_90: 10,
        days_91_180: 5,
      }),
    ).toBe(20);
  });

  it('treats empty and null values as zero', () => {
    expect(
      evaluateCalculatedExpression('a + b + c', {
        a: '',
        b: null,
        c: 7,
      }),
    ).toBe(7);
  });

  it('can evaluate root paths from a nested calculated field context', () => {
    expect(
      evaluateCalculatedExpression(
        '$.accrualSummary.buGroupSummary.FCTL.totalAccrued + $.accrualSummary.buGroupSummary.MSOL.totalAccrued',
        {},
        {
          accrualSummary: {
            buGroupSummary: {
              FCTL: { totalAccrued: 10 },
              MSOL: { totalAccrued: 20 },
            },
          },
        },
      ),
    ).toBe(30);
  });

  it('does not clone unchanged form data when no calculated fields are configured', () => {
    const schema = {
      type: 'object',
      properties: {
        amount: { type: 'number' },
      },
    };
    const formData = { amount: 100 };

    expect(applyCalculatedFields(schema, {}, formData)).toEqual({
      formState: formData,
      stabilized: true,
    });
  });

  it('creates and calculates TOTAL objects with root-path expressions', () => {
    const schema = {
      type: 'object',
      properties: {
        accrualSummary: {
          type: 'object',
          properties: {
            buGroupSummary: {
              type: 'object',
              properties: {
                FCTL: {
                  type: 'object',
                  properties: {
                    totalAccrued: { type: 'number' },
                  },
                },
                MSOL: {
                  type: 'object',
                  properties: {
                    totalAccrued: { type: 'number' },
                  },
                },
                SYSS: {
                  type: 'object',
                  properties: {
                    totalAccrued: { type: 'number' },
                  },
                },
                TOTAL: {
                  type: 'object',
                  properties: {
                    totalAccrued: { type: 'number' },
                  },
                },
              },
            },
            totalAccrued: { type: 'number' },
          },
        },
      },
    };
    const uiSchema = {
      accrualSummary: {
        buGroupSummary: {
          TOTAL: {
            totalAccrued: {
              'ui:field': 'calculated',
              'ui:options': {
                expression:
                  '$.accrualSummary.buGroupSummary.FCTL.totalAccrued + $.accrualSummary.buGroupSummary.MSOL.totalAccrued + $.accrualSummary.buGroupSummary.SYSS.totalAccrued',
              },
            },
          },
        },
        totalAccrued: {
          'ui:field': 'calculated',
          'ui:options': {
            expression: 'buGroupSummary.TOTAL.totalAccrued',
          },
        },
      },
    };

    expect(
      applyCalculatedFields(schema, uiSchema, {
        accrualSummary: {
          buGroupSummary: {
            FCTL: { totalAccrued: 10 },
            MSOL: { totalAccrued: 20 },
            SYSS: { totalAccrued: 30 },
          },
        },
      }),
    ).toEqual({
      formState: {
        accrualSummary: {
          buGroupSummary: {
            FCTL: { totalAccrued: 10 },
            MSOL: { totalAccrued: 20 },
            SYSS: { totalAccrued: 30 },
            TOTAL: { totalAccrued: 60 },
          },
          totalAccrued: 60,
        },
      },
      stabilized: true,
    });
  });

  it('calculates nested fields before parent totals', () => {
    const schema = {
      type: 'object',
      properties: {
        accrualSummary: {
          type: 'object',
          properties: {
            buGroupSummary: {
              type: 'object',
              properties: {
                FCTL: {
                  type: 'object',
                  properties: {
                    days_0_90: { type: 'number' },
                    days_91_180: { type: 'number' },
                    days_181_365: { type: 'number' },
                    over1Year: { type: 'number' },
                    totalAccrued: { type: 'number' },
                  },
                },
                MSOL: {
                  type: 'object',
                  properties: {
                    totalAccrued: { type: 'number' },
                  },
                },
              },
            },
            totalAccrued: { type: 'number' },
          },
        },
      },
    };
    const uiSchema = {
      accrualSummary: {
        buGroupSummary: {
          FCTL: {
            totalAccrued: {
              'ui:field': 'calculated',
              'ui:options': {
                expression:
                  'days_0_90 + days_91_180 + days_181_365 + over1Year',
              },
            },
          },
        },
        totalAccrued: {
          'ui:field': 'calculated',
          'ui:options': {
            expression:
              'buGroupSummary.FCTL.totalAccrued + buGroupSummary.MSOL.totalAccrued',
          },
        },
      },
    };
    const formData = {
      accrualSummary: {
        buGroupSummary: {
          FCTL: {
            days_0_90: 1000,
            days_91_180: 200,
            days_181_365: null,
            over1Year: '',
          },
          MSOL: {
            totalAccrued: 50,
          },
        },
      },
    };

    expect(applyCalculatedFields(schema, uiSchema, formData)).toEqual({
      formState: {
        accrualSummary: {
          buGroupSummary: {
            FCTL: {
              days_0_90: 1000,
              days_91_180: 200,
              days_181_365: null,
              over1Year: '',
              totalAccrued: 1200,
            },
            MSOL: {
              totalAccrued: 50,
            },
          },
          totalAccrued: 1250,
        },
      },
      stabilized: true,
    });
  });

  it('re-runs calculations when a field depends on a later sibling', () => {
    const schema = {
      type: 'object',
      properties: {
        grandTotal: { type: 'number' },
        subtotal: { type: 'number' },
        tax: { type: 'number' },
        base: { type: 'number' },
        fee: { type: 'number' },
      },
    };
    const uiSchema = {
      grandTotal: {
        'ui:field': 'calculated',
        'ui:options': {
          expression: 'subtotal + tax',
        },
      },
      subtotal: {
        'ui:field': 'calculated',
        'ui:options': {
          expression: 'base + fee',
        },
      },
    };

    expect(
      applyCalculatedFields(schema, uiSchema, {
        base: 10,
        fee: 5,
        tax: 2,
      }),
    ).toEqual({
      formState: {
        base: 10,
        fee: 5,
        tax: 2,
        subtotal: 15,
        grandTotal: 17,
      },
      stabilized: true,
    });
  });

  it('returns a warning instead of throwing when calculations do not stabilize', () => {
    const schema = {
      type: 'object',
      properties: {
        a: { type: 'number' },
        b: { type: 'number' },
      },
    };
    const uiSchema = {
      a: {
        'ui:field': 'calculated',
        'ui:options': {
          expression: 'b + 1',
        },
      },
      b: {
        'ui:field': 'calculated',
        'ui:options': {
          expression: 'a + 1',
        },
      },
    };

    expect(applyCalculatedFields(schema, uiSchema, {})).toEqual({
      formState: { a: 5, b: 6 },
      stabilized: false,
      warning:
        'Could not calculate value. Check expression for circular dependencies.',
    });
  });
});
