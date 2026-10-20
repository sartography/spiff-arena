import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import CustomForm from '../../../components/CustomForm';
import i18next from '../../../i18n';

const renderRangeForm = ({
  options,
  formData = {},
  rangeSchema = {},
  required = false,
  noValidate = false,
}: {
  options?: any;
  formData?: any;
  rangeSchema?: any;
  required?: boolean;
  noValidate?: boolean;
} = {}) => {
  const onChange = vi.fn();
  const onSubmit = vi.fn();
  render(
    <CustomForm
      id="range-form"
      key="range-form"
      formData={formData}
      noValidate={noValidate}
      onChange={onChange}
      onSubmit={onSubmit}
      schema={{
        type: 'object',
        required: required ? ['compensation'] : [],
        properties: {
          compensation: {
            title: 'Compensation',
            type: 'object',
            minimum: 0,
            maximum: 999999,
            properties: {
              min: { type: 'number' },
              max: { title: 'Highest', type: 'number' },
            },
            ...rangeSchema,
          },
        },
      }}
      uiSchema={{
        compensation: {
          'ui:field': 'numeric-range',
          ...(options ? { 'ui:options': options } : {}),
        },
      }}
    >
      <button type="submit">Submit</button>
    </CustomForm>,
  );
  return {
    minInput: screen.getByLabelText('Minimum') as HTMLInputElement,
    maxInput: screen.getByLabelText('Highest') as HTMLInputElement,
    onChange,
    onSubmit,
  };
};

const enter = (input: HTMLElement, text: string) => {
  fireEvent.focus(input);
  fireEvent.change(input, { target: { value: text } });
  fireEvent.blur(input);
};

const submit = () => fireEvent.click(screen.getByText('Submit'));

describe('NumericRangeField', () => {
  beforeEach(async () => {
    await i18next.changeLanguage('en-US');
  });

  afterEach(async () => {
    cleanup();
    await i18next.changeLanguage('en-US');
  });

  it('stores both ends under the field and submits them', () => {
    const { minInput, maxInput, onSubmit } = renderRangeForm();
    expect(minInput.id).toBe('root_compensation_min');
    expect(maxInput.id).toBe('root_compensation_max');

    enter(minInput, '1,000.5');
    enter(maxInput, '2000');
    expect(minInput).toHaveValue('1,000.5');
    expect(maxInput).toHaveValue('2,000');

    submit();
    expect(onSubmit.mock.calls[0][0].formData).toEqual({
      compensation: { min: 1000.5, max: 2000 },
    });
  });

  it('follows the user language for entry and bounds', async () => {
    await i18next.changeLanguage('de');
    const { minInput, onSubmit } = renderRangeForm({
      formData: { compensation: { max: 250000 } },
    });
    expect(screen.getByLabelText('Highest')).toHaveValue('250.000');
    expect(screen.getByText('Max: 999.999')).toBeInTheDocument();

    enter(minInput, '1.000,5');
    expect(minInput).toHaveValue('1.000,5');
    submit();
    expect(onSubmit.mock.calls[0][0].formData).toEqual({
      compensation: { min: 1000.5, max: 250000 },
    });
  });

  it('blocks submission of notation from another locale', () => {
    const { minInput, onChange, onSubmit } = renderRangeForm({
      options: { locale: 'de-DE' },
    });
    enter(minInput, '1,000.5');
    expect(minInput).toHaveAttribute('aria-invalid', 'true');
    expect(
      onChange.mock.calls[onChange.mock.calls.length - 1][0].formData,
    ).toEqual({ compensation: { min: { invalidNumberText: '1,000.5' } } });

    submit();
    expect(onSubmit).not.toHaveBeenCalled();
    expect(
      screen.getByText('Minimum: Invalid number. Example: 1.234.567,89'),
    ).toBeInTheDocument();
    expect(screen.queryByText(/must (be|have valid)/)).not.toBeInTheDocument();
  });

  it('applies decimals and currency, and reformats on a language switch', async () => {
    await i18next.changeLanguage('de');
    const { minInput, maxInput, onSubmit } = renderRangeForm({
      options: { decimals: 2, currency: 'EUR' },
    });
    enter(minInput, '1.000,5');
    enter(maxInput, '250.000');
    expect(minInput).toHaveValue('1.000,50');
    expect(maxInput).toHaveValue('250.000,00');
    expect(screen.getAllByText('€')).toHaveLength(2);

    await act(async () => {
      await i18next.changeLanguage('en-US');
    });
    expect(minInput).toHaveValue('1,000.50');
    expect(maxInput).toHaveValue('250,000.00');
    expect(screen.getByText('Max: 999,999')).toBeInTheDocument();
    submit();
    expect(onSubmit.mock.calls[0][0].formData.compensation).toEqual({
      min: 1000.5,
      max: 250000,
    });
  });

  it.each(['number', 'string'])(
    'keeps invalid %s drafts through autosave and reload',
    (type) => {
      const rangeSchema = {
        properties: { min: { type }, max: { type, title: 'Highest' } },
      };
      const options = { locale: 'de-DE', decimals: 2 };
      const { minInput, onChange } = renderRangeForm({ rangeSchema, options });
      enter(minInput, '100.5');
      const draft = onChange.mock.calls.at(-1)![0].formData;
      expect(draft.compensation.min).toEqual({ invalidNumberText: '100.5' });

      cleanup();
      const { onSubmit: onAutosave } = renderRangeForm({
        rangeSchema,
        options,
        formData: draft,
        noValidate: true,
      });
      submit();
      const saved = JSON.parse(
        JSON.stringify(onAutosave.mock.calls[0][0].formData),
      );
      expect(saved).toEqual(draft);

      cleanup();
      const { minInput: reloaded, onSubmit } = renderRangeForm({
        rangeSchema,
        options,
        formData: saved,
      });
      expect(reloaded).toHaveValue('100.5');
      expect(reloaded).toHaveAttribute('aria-invalid', 'true');
      submit();
      expect(onSubmit).not.toHaveBeenCalled();
      expect(
        screen.queryByText(/must (be|have valid)/),
      ).not.toBeInTheDocument();
    },
  );

  it('stores ranges at their full path in repeating sections', () => {
    const onSubmit = vi.fn();
    render(
      <CustomForm
        id="nested-form"
        key="nested-form"
        formData={{
          rows: [{ compensation: {} }, { compensation: { min: 20, max: 30 } }],
        }}
        schema={{
          type: 'object',
          properties: {
            rows: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  compensation: {
                    type: 'object',
                    minimum: 0,
                    maximum: 100,
                    properties: {
                      min: { type: 'number' },
                      max: { type: 'number' },
                    },
                  },
                },
              },
            },
          },
        }}
        uiSchema={{
          rows: { items: { compensation: { 'ui:field': 'numeric-range' } } },
        }}
        onSubmit={onSubmit}
      >
        <button type="submit">Submit</button>
      </CustomForm>,
    );
    const [firstMin, secondMin] = screen.getAllByLabelText('Minimum');
    const [firstMax, secondMax] = screen.getAllByLabelText('Maximum');
    expect(firstMin.id).toBe('root_rows_0_compensation_min');
    expect(secondMin.id).toBe('root_rows_1_compensation_min');
    enter(firstMin, '1');
    enter(firstMax, '10');
    enter(secondMax, '40');
    submit();
    expect(onSubmit.mock.calls[0][0].formData).toEqual({
      rows: [
        { compensation: { min: 1, max: 10 } },
        { compensation: { min: 20, max: 40 } },
      ],
    });

    onSubmit.mockClear();
    enter(secondMin, '50');
    submit();
    expect(onSubmit).not.toHaveBeenCalled();
    enter(secondMin, 'wrong');
    submit();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('honors integer endpoint schemas', () => {
    const { minInput, onSubmit } = renderRangeForm({
      options: { locale: 'de-DE' },
      rangeSchema: {
        properties: {
          min: { type: 'integer' },
          max: { type: 'integer', title: 'Highest' },
        },
      },
    });
    expect(minInput).toHaveAttribute('inputmode', 'numeric');
    enter(minInput, '1,5');
    submit();
    expect(onSubmit).not.toHaveBeenCalled();
    enter(minInput, '1.500');
    submit();
    expect(onSubmit.mock.calls[0][0].formData.compensation.min).toBe(1500);
  });

  it('validates null draft endpoints without crashing', () => {
    const { onSubmit } = renderRangeForm({
      formData: { compensation: { min: null, max: null } },
      required: true,
    });
    submit();
    expect(onSubmit).not.toHaveBeenCalled();
    expect(
      screen.getAllByText(/must have valid Minimum and Maximum/).length,
    ).toBeGreaterThan(0);
  });

  it.each([false, true])(
    'handles an absent range (required: %s)',
    (required) => {
      const { onSubmit } = renderRangeForm({ required });
      submit();
      expect(onSubmit).toHaveBeenCalledTimes(required ? 0 : 1);
    },
  );

  it('accepts small numeric values stored in exponent notation', () => {
    const { minInput, maxInput, onSubmit } = renderRangeForm();
    enter(minInput, '0.0000001');
    enter(maxInput, '0.0000002');
    submit();
    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0].formData.compensation).toEqual({
      min: 1e-7,
      max: 2e-7,
    });
  });

  it('compares string-schema endpoints numerically', () => {
    const { minInput, maxInput, onSubmit } = renderRangeForm({
      rangeSchema: {
        properties: {
          min: { type: 'string' },
          max: { title: 'Highest', type: 'string' },
        },
      },
    });
    enter(minInput, '9');
    enter(maxInput, '10');
    submit();
    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0].formData.compensation).toEqual({
      min: '9',
      max: '10',
    });

    onSubmit.mockClear();
    enter(minInput, '10');
    enter(maxInput, '9');
    submit();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it.each([
    ['min', '1'],
    ['min', '21'],
    ['max', '1'],
    ['max', '21'],
  ])('checks the range bounds for %s = %s', (end, text) => {
    const { minInput, maxInput, onSubmit } = renderRangeForm({
      rangeSchema: { minimum: 2, maximum: 20 },
    });
    enter(end === 'min' ? minInput : maxInput, text);
    submit();
    expect(onSubmit).not.toHaveBeenCalled();
    expect(
      screen.getAllByText(new RegExp(`must have ${end} (greater|less)`)).length,
    ).toBeGreaterThan(0);
  });

  it('keeps the range checks', () => {
    const { minInput, maxInput, onSubmit } = renderRangeForm();
    enter(minInput, '-5');
    expect(minInput).toHaveAttribute('aria-invalid', 'true');

    enter(minInput, '5');
    enter(maxInput, '2');
    submit();
    expect(onSubmit).not.toHaveBeenCalled();
    expect(
      screen.getAllByText(/must have min less than or equal to max/).length,
    ).toBeGreaterThan(0);
  });
});
