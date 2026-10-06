import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import CustomForm from '../components/CustomForm';
import i18next from '../i18n';
import { FormattedNumberWidget } from './formEnhancements';

const renderAmountForm = ({
  amountSchema = { type: 'number' },
  options = {},
  formData = {},
  onSubmit = vi.fn(),
  onChange,
  noValidate,
}: {
  amountSchema?: any;
  options?: any;
  formData?: any;
  onSubmit?: ReturnType<typeof vi.fn>;
  onChange?: ReturnType<typeof vi.fn>;
  noValidate?: boolean;
}) => {
  render(
    <CustomForm
      id="amount-form"
      key="amount-form"
      formData={formData}
      onChange={onChange}
      noValidate={noValidate}
      schema={{
        type: 'object',
        properties: { amount: { title: 'Amount', ...amountSchema } },
      }}
      uiSchema={{
        amount: { 'ui:widget': 'formattedNumber', 'ui:options': options },
      }}
      onSubmit={onSubmit}
    >
      <button type="submit">Submit</button>
    </CustomForm>,
  );
  return { input: screen.getByLabelText('Amount'), onSubmit };
};

const typeAndBlur = (input: HTMLElement, text: string) => {
  fireEvent.focus(input);
  fireEvent.change(input, { target: { value: text } });
  fireEvent.blur(input);
};

const submit = () => fireEvent.click(screen.getByText('Submit'));

describe('FormattedNumberWidget', () => {
  afterEach(async () => {
    // Unmount first so the language switch does not re-render live forms.
    cleanup();
    await i18next.changeLanguage('en-US');
  });

  it('stores German notation as a JSON number', () => {
    const { input, onSubmit } = renderAmountForm({
      options: { locale: 'de-DE', decimals: 2 },
    });

    typeAndBlur(input, '100.000');
    expect(input).toHaveValue('100.000,00');

    submit();
    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0].formData).toEqual({ amount: 100000 });
  });

  it('shows US notation in a German field as invalid and blocks submission', () => {
    const { input, onSubmit } = renderAmountForm({
      options: { locale: 'de-DE', decimals: 2 },
    });

    typeAndBlur(input, '100.5');
    expect(input).toHaveValue('100.5');
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(
      screen.getByText('Invalid number. Example: 1.234.567,89'),
    ).toBeInTheDocument();

    submit();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('blocks submission of invalid text in string schemas', () => {
    const { input, onSubmit } = renderAmountForm({
      amountSchema: { type: 'string' },
      options: { locale: 'de-DE' },
    });

    typeAndBlur(input, '1.50');
    submit();
    expect(onSubmit).not.toHaveBeenCalled();

    typeAndBlur(input, '1,50');
    submit();
    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0].formData).toEqual({ amount: '1.50' });
  });

  it('follows the user language when no locale is set', async () => {
    await i18next.changeLanguage('de');
    const { input } = renderAmountForm({ formData: { amount: 1234.5 } });
    expect(input).toHaveValue('1.234,5');
  });

  it('shows the currency symbol without storing it', () => {
    const { input, onSubmit } = renderAmountForm({
      options: { locale: 'de-DE', currency: 'EUR' },
    });
    expect(screen.getByText('€')).toBeInTheDocument();

    typeAndBlur(input, '12,5');
    submit();
    expect(onSubmit.mock.calls[0][0].formData).toEqual({ amount: 12.5 });
  });

  describe('with delayed echoes of emitted values', () => {
    const widgetProps = (value?: any): any => ({
      id: 'amount',
      label: 'Amount',
      schema: { type: 'number' },
      uiSchema: {},
      options: { locale: 'de-DE', decimals: 2 },
      onChange: vi.fn(),
      onBlur: vi.fn(),
      onFocus: vi.fn(),
      value,
    });

    const typeThenEcho = (
      initialValue: any,
      typed: string[],
      echoes: any[],
    ) => {
      const props = widgetProps(initialValue);
      const { rerender } = render(<FormattedNumberWidget {...props} />);
      const input = screen.getByLabelText('Amount');
      fireEvent.focus(input);
      typed.forEach((text) => {
        fireEvent.change(input, { target: { value: text } });
      });
      echoes.forEach((echo) => {
        rerender(<FormattedNumberWidget {...props} value={echo} />);
        expect(input).toHaveValue(typed[typed.length - 1]);
      });
      return { input, props, rerender };
    };

    it('keeps typed text while older values arrive', () => {
      const { input, props, rerender } = typeThenEcho(
        undefined,
        ['1', '10', '100', '100,', '100,5'],
        [1, 10, 100, 100, 100.5],
      );
      fireEvent.blur(input);
      expect(input).toHaveValue('100,50');

      rerender(<FormattedNumberWidget {...props} value={7} />);
      expect(input).toHaveValue('7,00');
    });

    it('keeps invalid text when an echo returns to the starting value', () => {
      const { input } = typeThenEcho(
        undefined,
        ['1', '', '100.5'],
        [1, undefined, { invalidNumberText: '100.5' }],
      );
      fireEvent.blur(input);
      expect(input).toHaveValue('100.5');
      expect(input).toHaveAttribute('aria-invalid', 'true');
    });

    it('keeps typed text when editing back through an earlier value', () => {
      const { input } = typeThenEcho(1, ['10', '1', '12'], [10, 1, 12]);
      expect(input).toHaveValue('12');
    });
  });

  it('shows prefilled float noise rounded and submits it unchanged', () => {
    const { input, onSubmit } = renderAmountForm({
      options: { locale: 'de-DE', decimals: 2 },
      formData: { amount: 1.1 * 3 },
    });
    expect(input).toHaveValue('3,30');
    expect(input).toHaveAttribute('aria-invalid', 'false');

    fireEvent.focus(input);
    fireEvent.blur(input);
    submit();
    expect(onSubmit.mock.calls[0][0].formData).toEqual({ amount: 1.1 * 3 });
  });

  it('stores invalid text that becomes valid after a language switch', async () => {
    await i18next.changeLanguage('de');
    const { input, onSubmit } = renderAmountForm({});
    typeAndBlur(input, '100.5');
    expect(input).toHaveAttribute('aria-invalid', 'true');

    await act(async () => {
      await i18next.changeLanguage('en-US');
    });
    expect(input).toHaveValue('100.5');
    expect(input).toHaveAttribute('aria-invalid', 'false');
    submit();
    expect(onSubmit.mock.calls[0][0].formData).toEqual({ amount: 100.5 });
  });

  it.each([
    ['number', '100.5'],
    ['string', '1.50'],
  ])(
    'keeps invalid text in a %s field through save and reload',
    (schemaType, invalidText) => {
      const amountSchema = { type: schemaType };
      const options = { locale: 'de-DE' };
      const onChange = vi.fn();
      const { input } = renderAmountForm({ amountSchema, options, onChange });
      typeAndBlur(input, invalidText);
      const draft =
        onChange.mock.calls[onChange.mock.calls.length - 1][0].formData;
      expect(draft).toEqual({ amount: { invalidNumberText: invalidText } });

      // The hidden autosave form submits without validation.
      cleanup();
      const onAutosave = vi.fn();
      renderAmountForm({
        amountSchema,
        options,
        formData: draft,
        onSubmit: onAutosave,
        noValidate: true,
      });
      submit();
      const saved = onAutosave.mock.calls[0][0].formData;
      expect(saved).toEqual(draft);

      cleanup();
      const onSubmit = vi.fn();
      const { input: reloaded } = renderAmountForm({
        amountSchema,
        options,
        formData: saved,
        onSubmit,
      });
      expect(reloaded).toHaveValue(invalidText);
      expect(reloaded).toHaveAttribute('aria-invalid', 'true');
      submit();
      expect(onSubmit).not.toHaveBeenCalled();
      expect(screen.queryByText(/must be/)).not.toBeInTheDocument();
    },
  );
});

describe('CalculatedField locale', () => {
  it('formats currency in the field locale', () => {
    render(
      <CustomForm
        id="calculated-form"
        key="calculated-form"
        formData={{ a: 60000, b: 40000 }}
        schema={{
          type: 'object',
          properties: {
            a: { type: 'number' },
            b: { type: 'number' },
            total: { title: 'Total', type: 'number' },
          },
        }}
        uiSchema={{
          total: {
            'ui:field': 'calculated',
            'ui:options': {
              expression: 'a + b',
              format: 'currency',
              currency: 'EUR',
              locale: 'de-DE',
            },
          },
        }}
      />,
    );
    expect(
      (screen.getByLabelText('Total') as HTMLInputElement).value.replace(
        /\s/g,
        ' ',
      ),
    ).toBe('100.000,00 €');
  });
});
