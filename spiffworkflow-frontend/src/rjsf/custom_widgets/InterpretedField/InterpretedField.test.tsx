import { act, fireEvent, render, screen } from '@testing-library/react';
import { useState } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import enUS from '../../../locales/en_us/translation.json';
import CustomForm from '../../../components/CustomForm';

// Resolve translation keys through the English dictionary so assertions
// read as user-facing text while still proving the keys exist.
vi.mock('react-i18next', async (importOriginal) => ({
  ...((await importOriginal()) as object),
  useTranslation: () => ({
    t: (key: string) => (enUS as Record<string, string>)[key] ?? key,
  }),
}));

const { makeCallToBackend } = vi.hoisted(() => ({
  makeCallToBackend: vi.fn(),
}));

vi.mock('../../../services/HttpService', () => ({
  default: { makeCallToBackend },
}));

// A fictional resolver: shouting text. Deliberately free of any domain
// vocabulary so the generic field contract stays generic.
const schema = {
  type: 'object',
  properties: {
    shout: {
      title: 'Shout',
      type: 'object',
      required: ['text'],
      properties: {
        expression: { type: 'string' },
        text: { type: 'string' },
      },
    },
  },
};

const uiSchema = {
  shout: {
    'ui:field': 'interpreted-field',
    'ui:options': {
      resolver: 'shout',
      exclamation_marks: 3,
      idleMilliseconds: 500,
      placeholder: 'Say something',
      examples: 'Examples: hello, good morning',
      emptyMessage: 'Say something first.',
      suggestions: ['hello', 'good morning'],
      editSchema: {
        type: 'object',
        properties: {
          text: { type: 'string', title: 'Shouted text' },
        },
      },
      valueDefaults: { text: '' },
    },
  },
};

const validShoutResult = {
  status: 'valid',
  value: { expression: 'hello', text: 'HELLO!!!' },
  preview: 'HELLO!!!',
  detail: '8 characters',
  assumptions: ['assuming English'],
  edit_defaults: { text: 'HELLO!!!' },
};

describe('InterpretedField', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-08-30T18:00:00Z'));
    makeCallToBackend.mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('stores a valid resolver result and renders its preview', () => {
    const onChange = vi.fn();
    render(
      <CustomForm
        id="shout-form"
        key="shout-form"
        formData={{}}
        schema={schema}
        uiSchema={uiSchema}
        onChange={onChange}
      />,
    );

    const input = screen.getByRole('textbox', { name: 'Shout' });
    fireEvent.change(input, { target: { value: 'hello' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(makeCallToBackend).toHaveBeenCalledTimes(1);
    const request = makeCallToBackend.mock.calls[0][0];
    expect(request.path).toBe('/v1.0/extensions/shout');
    // Deployment options flow through; field configuration does not.
    expect(request.postBody.extension_input).toEqual(
      expect.objectContaining({
        expression: 'hello',
        exclamation_marks: 3,
        reference_instant: '2026-08-30T18:00:00.000Z',
        time_zone: expect.any(String),
        locale: expect.any(String),
      }),
    );
    expect(request.postBody.extension_input).not.toHaveProperty('resolver');
    expect(request.postBody.extension_input).not.toHaveProperty('suggestions');
    expect(request.postBody.extension_input).not.toHaveProperty('editSchema');
    // A fresh expression parse carries an empty value for validation.
    expect(request.postBody.extension_input.value).toEqual({});

    act(() => {
      request.successCallback({ task_data: { result: validShoutResult } });
    });

    expect(onChange).toHaveBeenLastCalledWith(
      expect.objectContaining({
        formData: { shout: validShoutResult.value },
      }),
      expect.anything(),
    );
    expect(screen.getByText('HELLO!!!')).toBeVisible();
    expect(screen.getByText('8 characters')).toBeVisible();
    expect(screen.getByText('assuming English')).toBeVisible();
  });

  it('fills configured value defaults including the browser zone token', () => {
    const onChange = vi.fn();
    render(
      <CustomForm
        id="defaults-form"
        key="defaults-form"
        formData={{}}
        schema={{
          type: 'object',
          properties: {
            shout: {
              title: 'Shout',
              type: 'object',
              properties: {
                expression: { type: 'string' },
                text: { type: 'string' },
                zone: { type: 'string' },
              },
            },
          },
        }}
        uiSchema={{
          shout: {
            'ui:field': 'interpreted-field',
            'ui:options': {
              resolver: 'shout',
              valueDefaults: {
                zone: '$browserTimeZone',
                text: 'hi',
              },
            },
          },
        }}
        onChange={onChange}
      />,
    );

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        formData: {
          shout: {
            zone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            text: 'hi',
          },
        },
      }),
      expect.anything(),
    );
  });

  it('does not raise form-level errors while typing', () => {
    render(
      <CustomForm
        id="shout-form"
        key="shout-form"
        formData={{}}
        schema={schema}
        uiSchema={uiSchema}
        onChange={vi.fn()}
      />,
    );

    const input = screen.getByRole('textbox', { name: 'Shout' });
    fireEvent.change(input, { target: { value: 'hel' } });

    // Typing must not flag the input or hoist an Errors panel above the
    // form, which would shove the input being typed into down the page.
    expect(input).toHaveAttribute('aria-invalid', 'false');
    expect(screen.queryByText('Errors')).toBeNull();

    act(() => {
      vi.advanceTimersByTime(500);
    });
    act(() => {
      makeCallToBackend.mock.calls[0][0].successCallback({
        task_data: {
          result: {
            status: 'invalid',
            errors: [{ code: 'unclear', message: 'Speak up.' }],
          },
        },
      });
    });

    // A settled invalid interpretation still surfaces normally.
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getAllByText('Speak up.').length).toBeGreaterThan(0);
  });

  it('parses a suggestion chip immediately on click', () => {
    render(
      <CustomForm
        id="shout-form"
        key="shout-form"
        formData={{}}
        schema={schema}
        uiSchema={uiSchema}
        onChange={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByText('good morning'));

    expect(makeCallToBackend).toHaveBeenCalledTimes(1);
    expect(
      makeCallToBackend.mock.calls[0][0].postBody.extension_input.expression,
    ).toBe('good morning');
  });

  it('offers resolver choices and revalidates the chosen value', () => {
    const onChange = vi.fn();
    render(
      <CustomForm
        id="shout-form"
        key="shout-form"
        formData={{}}
        schema={schema}
        uiSchema={uiSchema}
        onChange={onChange}
      />,
    );

    const input = screen.getByRole('textbox', { name: 'Shout' });
    fireEvent.change(input, { target: { value: 'hello' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    const choiceValue = { expression: 'hello', text: 'HELLO?' };
    act(() => {
      makeCallToBackend.mock.calls[0][0].successCallback({
        task_data: {
          result: {
            status: 'ambiguous',
            errors: [{ code: 'uncertain', message: 'Loud or louder?' }],
            choices: [
              {
                label: 'Loud',
                detail: 'Three marks',
                value: choiceValue,
                assumptions: ['assuming loud'],
              },
            ],
          },
        },
      });
    });

    expect(screen.getByText('Which did you mean?')).toBeVisible();
    fireEvent.click(screen.getByText('Loud'));

    expect(makeCallToBackend).toHaveBeenCalledTimes(2);
    const second = makeCallToBackend.mock.calls[1][0];
    expect(second.postBody.extension_input.value).toEqual(choiceValue);

    act(() => {
      second.successCallback({
        task_data: {
          result: {
            status: 'valid',
            value: choiceValue,
            preview: 'HELLO?',
            assumptions: ['assuming loud'],
          },
        },
      });
    });
    expect(onChange).toHaveBeenLastCalledWith(
      expect.objectContaining({ formData: { shout: choiceValue } }),
      expect.anything(),
    );
  });

  it('applies manual edits by revalidating the edited value', () => {
    render(
      <CustomForm
        id="shout-form"
        key="shout-form"
        formData={{ shout: { expression: 'hello', text: 'HELLO!!!' } }}
        schema={schema}
        uiSchema={uiSchema}
        onChange={vi.fn()}
      />,
    );

    // Seed the editor from the resolver-provided edit defaults.
    makeCallToBackend.mockReset();
    const input = screen.getByRole('textbox', { name: 'Shout' });
    fireEvent.change(input, { target: { value: 'hello' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    act(() => {
      makeCallToBackend.mock.calls[0][0].successCallback({
        task_data: { result: validShoutResult },
      });
    });

    fireEvent.click(screen.getByText('Adjust values'));
    const editor = screen.getByRole('textbox', { name: 'Shouted text' });
    expect(editor).toHaveValue('HELLO!!!');
    fireEvent.change(editor, { target: { value: 'HI!!!' } });
    fireEvent.click(screen.getByText('Apply'));

    expect(makeCallToBackend).toHaveBeenCalledTimes(2);
    expect(
      makeCallToBackend.mock.calls[1][0].postBody.extension_input.value,
    ).toEqual({ text: 'HI!!!' });
  });

  it('blocks submission while the current expression is invalid', () => {
    const onSubmit = vi.fn();
    render(
      <CustomForm
        id="shout-form"
        key="shout-form"
        formData={{ shout: { text: 'HELLO!!!' } }}
        schema={schema}
        uiSchema={uiSchema}
        onSubmit={onSubmit}
      />,
    );

    const input = screen.getByRole('textbox', { name: 'Shout' });
    fireEvent.change(input, { target: { value: 'hello' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    act(() => {
      makeCallToBackend.mock.calls[0][0].successCallback({
        task_data: { result: validShoutResult },
      });
    });
    expect(screen.getByText('HELLO!!!')).toBeVisible();

    fireEvent.change(input, { target: { value: 'mumble' } });
    act(() => {
      vi.advanceTimersByTime(500);
    });
    act(() => {
      makeCallToBackend.mock.calls[1][0].successCallback({
        task_data: {
          result: {
            status: 'invalid',
            errors: [{ code: 'unclear', message: 'Speak up.' }],
          },
        },
      });
    });

    fireEvent.submit(document.querySelector('form')!);
    act(() => {
      vi.advanceTimersByTime(100);
    });

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByText('Speak up.')).toBeVisible();
    // The last valid interpretation stays visible but marked as stale.
    expect(screen.getByText('Last valid interpretation')).toBeVisible();
  });

  it('defers submission until a raced interpretation resolves', () => {
    const onSubmit = vi.fn();
    render(
      <CustomForm
        id="shout-form"
        key="shout-form"
        formData={{}}
        schema={schema}
        uiSchema={uiSchema}
        onSubmit={onSubmit}
      />,
    );

    const input = screen.getByRole('textbox', { name: 'Shout' });
    fireEvent.change(input, { target: { value: 'hello' } });
    fireEvent.submit(document.querySelector('form')!);

    expect(onSubmit).not.toHaveBeenCalled();
    expect(makeCallToBackend).toHaveBeenCalledTimes(1);

    act(() => {
      makeCallToBackend.mock.calls[0][0].successCallback({
        task_data: { result: validShoutResult },
      });
    });
    act(() => {
      vi.advanceTimersByTime(0);
    });

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0].formData).toEqual({
      shout: validShoutResult.value,
    });
  });

  it('does not re-parse on blur when the expression is unchanged', () => {
    render(
      <CustomForm
        id="shout-form"
        key="shout-form"
        formData={{ shout: { expression: 'hello', text: 'HELLO!!!' } }}
        schema={schema}
        uiSchema={uiSchema}
        onChange={vi.fn()}
      />,
    );

    const input = screen.getByRole('textbox', { name: 'Shout' });
    fireEvent.focus(input);
    fireEvent.blur(input);
    act(() => {
      vi.advanceTimersByTime(1000);
    });

    expect(makeCallToBackend).not.toHaveBeenCalled();
  });

  it('keeps existing values submittable after the expression is cleared', () => {
    function StatefulForm() {
      const [formData, setFormData] = useState({
        shout: { expression: 'hello', text: 'HELLO!!!' },
      });
      return (
        <CustomForm
          id="shout-form"
          key="shout-form"
          formData={formData}
          schema={schema}
          uiSchema={uiSchema}
          onChange={(event: any) => setFormData(event.formData)}
        />
      );
    }
    render(<StatefulForm />);

    const input = screen.getByRole('textbox', { name: 'Shout' });
    fireEvent.change(input, { target: { value: '' } });
    act(() => {
      vi.advanceTimersByTime(500);
    });

    expect(makeCallToBackend).not.toHaveBeenCalled();
    expect(screen.queryByText('Interpretation pending.')).toBeNull();
    expect(screen.queryByText('Say something first.')).toBeNull();
  });
});
