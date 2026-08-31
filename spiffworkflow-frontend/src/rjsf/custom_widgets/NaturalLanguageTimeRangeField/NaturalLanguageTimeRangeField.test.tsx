import { act, fireEvent, render, screen } from '@testing-library/react';
import { useState } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import CustomForm from '../../../components/CustomForm';

const NY_START = '2026-08-30T16:00:00Z';
const NY_END = '2026-08-30T17:00:00Z';

const { makeCallToBackend } = vi.hoisted(() => ({
  makeCallToBackend: vi.fn(),
}));

vi.mock('../../../services/HttpService', () => ({
  default: { makeCallToBackend },
}));

const schema = {
  type: 'object',
  properties: {
    work_period: {
      title: 'Work time',
      type: 'object',
      required: ['start', 'end', 'time_zone'],
      properties: {
        expression: { type: 'string' },
        start: { type: 'string', format: 'date-time' },
        end: { type: 'string', format: 'date-time' },
        time_zone: { type: 'string' },
      },
    },
  },
};

const uiSchema = {
  work_period: {
    'ui:field': 'natural-language-time-range',
    'ui:options': {
      resolver: 'natural-language-time-range',
      date_order: 'MDY',
      prefer_completed_range: true,
      maximum_hours: 16,
    },
  },
};

describe('NaturalLanguageTimeRangeField', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-08-30T18:00:00Z'));
    makeCallToBackend.mockReset();
    vi.spyOn(Intl.DateTimeFormat.prototype, 'resolvedOptions').mockReturnValue({
      locale: 'en-US',
      calendar: 'gregory',
      numberingSystem: 'latn',
      timeZone: 'America/New_York',
    });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('stores a valid extension result in the object field it owns', () => {
    const onChange = vi.fn();
    render(
      <CustomForm
        id="time-form"
        key="time-form"
        formData={{}}
        schema={schema}
        uiSchema={uiSchema}
        onChange={onChange}
      />,
    );

    const input = screen.getByRole('textbox', { name: 'Work time' });
    fireEvent.change(input, { target: { value: '12-1' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(makeCallToBackend).toHaveBeenCalledTimes(1);
    const request = makeCallToBackend.mock.calls[0][0];
    expect(request.path).toBe('/v1.0/extensions/natural-language-time-range');
    expect(request.postBody).toEqual({
      extension_input: {
        expression: '12-1',
        reference_instant: '2026-08-30T18:00:00.000Z',
        time_zone: expect.any(String),
        locale: 'en-US',
        date_order: 'MDY',
        prefer_completed_range: true,
        maximum_hours: 16,
      },
    });

    act(() => {
      request.successCallback({
        task_data: {
          result: {
            status: 'valid',
            value: {
              expression: '12-1',
              start: NY_START,
              end: NY_END,
              time_zone: 'America/New_York',
            },
            assumptions: ['assuming PM', 'today'],
          },
        },
      });
    });

    expect(onChange).toHaveBeenLastCalledWith(
      expect.objectContaining({
        formData: {
          work_period: {
            expression: '12-1',
            start: NY_START,
            end: NY_END,
            time_zone: 'America/New_York',
          },
        },
      }),
      expect.anything(),
    );
    expect(screen.getByText(/assuming PM, today/)).toBeVisible();
  });

  it('allows exact entry before a natural-language value has resolved', () => {
    render(
      <CustomForm
        id="time-form"
        key="time-form"
        formData={{}}
        schema={schema}
        uiSchema={uiSchema}
        onChange={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Edit exact times' }));

    expect(screen.getByLabelText('Exact start')).toHaveValue('');
    expect(screen.getByLabelText('Exact end')).toHaveValue('');
  });

  it('shows an existing range and reveals exact editing on demand', () => {
    render(
      <CustomForm
        id="time-form"
        key="time-form"
        formData={{
          work_period: {
            start: NY_START,
            end: NY_END,
            time_zone: 'UTC',
          },
        }}
        schema={schema}
        uiSchema={uiSchema}
        onChange={vi.fn()}
      />,
    );

    expect(screen.getByText(/Aug 30/)).toBeVisible();
    expect(screen.queryByLabelText('Exact start')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Edit exact times' }));

    expect(screen.getByLabelText('Exact start')).toHaveValue(
      '2026-08-30T16:00',
    );
    expect(screen.getByLabelText('Exact end')).toHaveValue('2026-08-30T17:00');
    expect(
      screen.getByRole('button', { name: 'Apply exact times' }),
    ).toBeVisible();
  });

  it('requires an offset choice for an exact time that occurs twice', () => {
    const onChange = vi.fn();
    render(
      <CustomForm
        id="time-form"
        key="time-form"
        formData={{
          work_period: {
            start: '2026-11-01T05:00:00Z',
            end: '2026-11-01T07:00:00Z',
            time_zone: 'America/New_York',
          },
        }}
        schema={schema}
        uiSchema={uiSchema}
        onChange={onChange}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Edit exact times' }));
    expect(screen.getByLabelText('Exact start')).toHaveValue(
      '2026-11-01T01:00',
    );
    expect(
      screen.getByRole('combobox', { name: 'Start UTC offset' }),
    ).toBeVisible();

    fireEvent.mouseDown(
      screen.getByRole('combobox', { name: 'Start UTC offset' }),
    );
    fireEvent.click(screen.getByRole('option', { name: 'UTC-04:00' }));
    fireEvent.click(screen.getByRole('button', { name: 'Apply exact times' }));

    expect(onChange).toHaveBeenLastCalledWith(
      expect.objectContaining({
        formData: expect.objectContaining({
          work_period: expect.objectContaining({
            start: '2026-11-01T05:00:00.000Z',
          }),
        }),
      }),
      expect.anything(),
    );
  });

  it('cancels stale requests and accepts only the latest result', () => {
    const onChange = vi.fn();
    render(
      <CustomForm
        id="time-form"
        key="time-form"
        formData={{}}
        schema={schema}
        uiSchema={uiSchema}
        onChange={onChange}
      />,
    );

    const input = screen.getByRole('textbox', { name: 'Work time' });
    fireEvent.change(input, { target: { value: '12-1' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    const firstRequest = makeCallToBackend.mock.calls[0][0];

    fireEvent.change(input, { target: { value: '3-5 8/12' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    const secondRequest = makeCallToBackend.mock.calls[1][0];
    expect(firstRequest.signal.aborted).toBe(true);

    const callsBeforeStaleResponse = onChange.mock.calls.length;
    act(() => {
      firstRequest.successCallback({
        task_data: {
          result: {
            status: 'valid',
            value: {
              expression: '12-1',
              start: NY_START,
              end: NY_END,
              time_zone: 'UTC',
            },
          },
        },
      });
    });
    expect(onChange).toHaveBeenCalledTimes(callsBeforeStaleResponse);

    act(() => {
      secondRequest.successCallback({
        task_data: {
          result: {
            status: 'valid',
            value: {
              expression: '3-5 8/12',
              start: '2026-08-12T19:00:00Z',
              end: '2026-08-12T21:00:00Z',
              time_zone: 'UTC',
            },
          },
        },
      });
    });
    expect(onChange).toHaveBeenLastCalledWith(
      expect.objectContaining({
        formData: expect.objectContaining({
          work_period: expect.objectContaining({ expression: '3-5 8/12' }),
        }),
      }),
      expect.anything(),
    );
  });

  it('keeps the last valid instants when a new expression is invalid', () => {
    const onChange = vi.fn();
    render(
      <CustomForm
        id="time-form"
        key="time-form"
        formData={{
          work_period: {
            expression: '12-1',
            start: NY_START,
            end: NY_END,
            time_zone: 'UTC',
          },
        }}
        schema={schema}
        uiSchema={uiSchema}
        onChange={onChange}
      />,
    );

    const input = screen.getByRole('textbox', { name: 'Work time' });
    fireEvent.change(input, { target: { value: 'not a range' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    act(() => {
      makeCallToBackend.mock.calls[0][0].successCallback({
        task_data: {
          result: {
            status: 'invalid',
            errors: [
              {
                code: 'invalid_expression',
                message: 'Enter a start and end time.',
              },
            ],
          },
        },
      });
    });

    expect(screen.getByText('Enter a start and end time.')).toBeVisible();
    expect(screen.getByText(/Aug 30/)).toBeVisible();
    expect(onChange).toHaveBeenLastCalledWith(
      expect.objectContaining({
        formData: {
          work_period: {
            expression: 'not a range',
            start: NY_START,
            end: NY_END,
            time_zone: 'UTC',
          },
        },
      }),
      expect.anything(),
    );
  });

  it('keeps a cleared expression submittable when valid instants remain', () => {
    const onChange = vi.fn();
    // Mirrors TaskShow, which feeds each change back into the form so the
    // rendered error state follows the field's emitted value.
    function StatefulForm() {
      const [formData, setFormData] = useState({
        work_period: {
          expression: '12-1',
          start: NY_START,
          end: NY_END,
          time_zone: 'UTC',
        },
      });
      return (
        <CustomForm
          id="time-form"
          key="time-form"
          formData={formData}
          schema={schema}
          uiSchema={uiSchema}
          onChange={(...args: any[]) => {
            onChange(...args);
            setFormData(args[0].formData);
          }}
        />
      );
    }
    render(<StatefulForm />);

    const input = screen.getByRole('textbox', { name: 'Work time' });
    fireEvent.change(input, { target: { value: '' } });
    act(() => {
      vi.advanceTimersByTime(500);
    });

    expect(makeCallToBackend).not.toHaveBeenCalled();
    expect(screen.queryByText('Interpretation pending.')).toBeNull();
    expect(screen.queryByText('Enter a time range.')).toBeNull();
    expect(screen.getByText(/Aug 30/)).toBeVisible();
    expect(onChange).toHaveBeenLastCalledWith(
      expect.objectContaining({
        formData: {
          work_period: {
            expression: '',
            start: NY_START,
            end: NY_END,
            time_zone: 'UTC',
          },
        },
      }),
      expect.anything(),
    );
  });

  it('does not re-parse on blur when the expression is unchanged', () => {
    render(
      <CustomForm
        id="time-form"
        key="time-form"
        formData={{
          work_period: {
            expression: '12-1',
            start: NY_START,
            end: NY_END,
            time_zone: 'UTC',
          },
        }}
        schema={schema}
        uiSchema={uiSchema}
        onChange={vi.fn()}
      />,
    );

    const input = screen.getByRole('textbox', { name: 'Work time' });
    fireEvent.focus(input);
    fireEvent.blur(input);
    act(() => {
      vi.advanceTimersByTime(1000);
    });

    expect(makeCallToBackend).not.toHaveBeenCalled();
  });

  it('defers submission until a raced interpretation resolves', () => {
    const onSubmit = vi.fn();
    render(
      <CustomForm
        id="time-form"
        key="time-form"
        formData={{}}
        schema={schema}
        uiSchema={uiSchema}
        onSubmit={onSubmit}
      />,
    );

    const input = screen.getByRole('textbox', { name: 'Work time' });
    fireEvent.change(input, { target: { value: '12-1' } });
    fireEvent.submit(document.querySelector('form')!);

    // The submit was held; the interpretation request went out immediately.
    expect(onSubmit).not.toHaveBeenCalled();
    expect(makeCallToBackend).toHaveBeenCalledTimes(1);

    act(() => {
      makeCallToBackend.mock.calls[0][0].successCallback({
        task_data: {
          result: {
            status: 'valid',
            value: {
              expression: '12-1',
              start: NY_START,
              end: NY_END,
              time_zone: 'America/New_York',
            },
            assumptions: [],
          },
        },
      });
    });
    act(() => {
      vi.advanceTimersByTime(0);
    });

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0].formData).toEqual({
      work_period: {
        expression: '12-1',
        start: NY_START,
        end: NY_END,
        time_zone: 'America/New_York',
      },
    });
  });

  it('blocks submission while the current expression is invalid', () => {
    const onSubmit = vi.fn();
    render(
      <CustomForm
        id="time-form"
        key="time-form"
        formData={{
          work_period: {
            start: NY_START,
            end: NY_END,
            time_zone: 'UTC',
          },
        }}
        schema={schema}
        uiSchema={uiSchema}
        onSubmit={onSubmit}
      />,
    );

    const input = screen.getByRole('textbox', { name: 'Work time' });
    fireEvent.change(input, { target: { value: 'banana' } });
    act(() => {
      vi.advanceTimersByTime(500);
    });
    act(() => {
      makeCallToBackend.mock.calls[0][0].successCallback({
        task_data: {
          result: {
            status: 'invalid',
            errors: [
              { code: 'invalid_expression', message: 'Enter a time range.' },
            ],
          },
        },
      });
    });

    fireEvent.submit(document.querySelector('form')!);
    act(() => {
      vi.advanceTimersByTime(100);
    });

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByText('Enter a time range.')).toBeVisible();
  });

  it('does not submit after an invalid interpretation that raced the submit', () => {
    const onSubmit = vi.fn();
    render(
      <CustomForm
        id="time-form"
        key="time-form"
        formData={{
          work_period: {
            start: NY_START,
            end: NY_END,
            time_zone: 'UTC',
          },
        }}
        schema={schema}
        uiSchema={uiSchema}
        onSubmit={onSubmit}
      />,
    );

    const input = screen.getByRole('textbox', { name: 'Work time' });
    fireEvent.change(input, { target: { value: 'not a range' } });
    fireEvent.submit(document.querySelector('form')!);

    act(() => {
      makeCallToBackend.mock.calls[0][0].successCallback({
        task_data: {
          result: {
            status: 'invalid',
            errors: [
              { code: 'invalid_expression', message: 'Enter a time range.' },
            ],
          },
        },
      });
    });
    act(() => {
      vi.advanceTimersByTime(0);
    });

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByText('Enter a time range.')).toBeVisible();
  });
});
