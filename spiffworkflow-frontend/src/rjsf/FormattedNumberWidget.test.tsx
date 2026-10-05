import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import CustomForm from '../components/CustomForm';
import i18next from '../i18n';
import { FormattedNumberWidget } from './formEnhancements';

const renderAmountForm = ({
  amountSchema = { type: 'number' },
  options = {},
  formData = {},
  onSubmit = vi.fn(),
}: {
  amountSchema?: any;
  options?: any;
  formData?: any;
  onSubmit?: ReturnType<typeof vi.fn>;
}) => {
  render(
    <CustomForm
      id="amount-form"
      key="amount-form"
      formData={formData}
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

  it('keeps typed text when older values are echoed back', () => {
    const props: any = {
      id: 'amount',
      label: 'Amount',
      schema: { type: 'number' },
      uiSchema: {},
      options: { locale: 'de-DE', decimals: 2 },
      onChange: vi.fn(),
      onBlur: vi.fn(),
      onFocus: vi.fn(),
    };
    const { rerender } = render(<FormattedNumberWidget {...props} />);
    const input = screen.getByLabelText('Amount');

    fireEvent.focus(input);
    ['1', '10', '100', '100,', '100,5'].forEach((text) => {
      fireEvent.change(input, { target: { value: text } });
    });
    [1, 10, 100].forEach((echo) => {
      rerender(<FormattedNumberWidget {...props} value={echo} />);
      expect(input).toHaveValue('100,5');
    });
    rerender(<FormattedNumberWidget {...props} value={100.5} />);
    fireEvent.blur(input);
    expect(input).toHaveValue('100,50');

    rerender(<FormattedNumberWidget {...props} value={7} />);
    expect(input).toHaveValue('7,00');
  });
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
