import { render, screen } from '@testing-library/react';
import { FieldProps } from '@rjsf/utils';
import { vi } from 'vitest';
import NumericRangeField from './NumericRangeField';

describe('NumericRangeField number formatting', () => {
  it.each([
    ['0', '0'],
    ['123', '123'],
    ['1234', '1,234'],
    ['123456', '123,456'],
    ['1234567.8900', '1,234,567.8900'],
    ['-1234567.5', '-1,234,567.5'],
    ['1,234,567', '1,234,567'],
    ['not a number', 'not a number'],
    ['1'.repeat(3000), Array(1000).fill('111').join(',')],
  ])(
    'groups integer digits without altering the fractional part',
    (value, expected) => {
      const props = {
        id: 'range',
        label: 'Range',
        schema: { type: 'object' },
        uiSchema: {},
        formData: { min: value, max: value },
        registry: { templates: { DescriptionFieldTemplate: () => null } },
        onChange: vi.fn(),
      } as unknown as FieldProps;

      render(<NumericRangeField {...props} />);

      expect(screen.getByLabelText('Minimum')).toHaveValue(expected);
      expect(screen.getByLabelText('Maximum')).toHaveValue(expected);
    },
  );
});
