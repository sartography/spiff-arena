import { describe, expect, it } from 'vitest';
import {
  applyCalculatedFields,
  coerceFormattedNumberValue,
  evaluateCalculatedExpression,
  formatNumberForDisplay,
  stripNumberFormatting,
} from './formEnhancements';

describe('formatted number helpers', () => {
  it('adds comma separators for large numbers', () => {
    expect(formatNumberForDisplay('1234567.89', { type: 'number' })).toBe(
      '1,234,567.89',
    );
  });

  it('submits numeric schema values as numbers', () => {
    expect(coerceFormattedNumberValue('1,234,567.89', { type: 'number' })).toBe(
      1234567.89,
    );
  });

  it('submits string schema values as unformatted numeric strings', () => {
    expect(coerceFormattedNumberValue('1,234', { type: 'string' })).toBe(
      '1234',
    );
  });

  it('preserves empty values as undefined', () => {
    expect(coerceFormattedNumberValue('', { type: 'number' })).toBeUndefined();
  });

  it('honors non-negative schemas when normalizing input', () => {
    expect(
      stripNumberFormatting('-1,234', { type: 'number', minimum: 0 }),
    ).toBe('1234');
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

    expect(applyCalculatedFields(schema, {}, formData)).toBe(formData);
  });

  it('creates and calculates Emerson-style TOTAL objects with root-path expressions', () => {
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
      accrualSummary: {
        buGroupSummary: {
          FCTL: { totalAccrued: 10 },
          MSOL: { totalAccrued: 20 },
          SYSS: { totalAccrued: 30 },
          TOTAL: { totalAccrued: 60 },
        },
        totalAccrued: 60,
      },
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
    });
  });
});
