import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import CustomForm from '../components/CustomForm';
import { BACKEND_BASE_URL } from '../config';

const digest = 'a'.repeat(64);
const stored = (name = 'sheet.xlsx', type = 'application/octet-stream') =>
  `data:${type};name=${encodeURIComponent(name)};base64,spifffiledatadigest+${digest}`;
const raw = 'data:text/plain;name=new.txt;base64,aGVsbG8=';

function renderForm({
  value = stored(),
  multiple = false,
  readonly = false,
  disabled = false,
  context = true,
  required = false,
}: {
  value?: string | string[];
  multiple?: boolean;
  readonly?: boolean;
  disabled?: boolean;
  context?: boolean;
  required?: boolean;
} = {}) {
  const onSubmit = vi.fn();
  const onChange = vi.fn();
  const fileSchema = { type: 'string', format: 'data-url', title: 'File' };
  const result = render(
    <CustomForm
      id="uploads"
      key="uploads"
      schema={{
        type: 'object',
        properties: {
          file: multiple ? { type: 'array', items: fileSchema } : fileSchema,
        },
        required: required ? ['file'] : [],
      }}
      uiSchema={{
        file: { 'ui:readonly': readonly, 'ui:options': { filePreview: true } },
      }}
      formData={{ file: value }}
      fileDownloadContext={
        context
          ? { process_model_identifier: 'group/model', process_instance_id: 42 }
          : undefined
      }
      disabled={disabled}
      onSubmit={onSubmit}
      onChange={onChange}
    >
      <button type="submit">Submit</button>
    </CustomForm>,
  );
  return { ...result, onSubmit, onChange };
}

describe('stored file references', () => {
  afterEach(cleanup);

  it.each([
    [
      'sheet.xlsx',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ],
    ['image.png', 'image/png'],
    [
      'Provisions [draft]; version=2.docx',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ],
  ])('downloads %s through the API, never as base64', (name, type) => {
    const value = stored(name, type);
    const { container, onSubmit } = renderForm({ value, required: true });
    expect(screen.getByRole('link', { name })).toHaveAttribute(
      'href',
      `${BACKEND_BASE_URL}/process-data-file-download/group:model/42/${digest}`,
    );
    expect(
      container.querySelector('[src^="data:"], a[href^="data:"]'),
    ).toBeNull();
    expect(screen.queryByText(/63 bytes/)).not.toBeInTheDocument();
    expect(container.querySelector('input[type=file]')).not.toBeRequired();
    fireEvent.click(screen.getByText('Submit'));
    expect(onSubmit.mock.calls[0][0].formData).toEqual({ file: value });
  });

  it.each([{ readonly: true }, { disabled: true }])(
    'does not offer removal for a read-only/disabled stored file: %j',
    (options) => {
      renderForm(options);
      expect(
        screen.queryByRole('button', { name: 'Remove' }),
      ).not.toBeInTheDocument();
      expect(
        screen.getByRole('link', { name: 'sheet.xlsx' }),
      ).toBeInTheDocument();
    },
  );

  it('does not invent a download URL without instance context', () => {
    const { container } = renderForm({ context: false });
    expect(screen.getByText('sheet.xlsx')).toBeInTheDocument();
    expect(container.querySelector('a, img')).toBeNull();
  });

  it('allows removing a stored file', () => {
    const { onChange } = renderForm();
    fireEvent.click(screen.getByRole('button', { name: 'Remove' }));
    expect(onChange.mock.calls.at(-1)?.[0].formData.file).toBeUndefined();
  });

  it('keeps stored references when removing a newly selected file from a mixed array', () => {
    const { onChange } = renderForm({ multiple: true, value: [stored(), raw] });
    fireEvent.click(screen.getAllByRole('button', { name: 'Remove' })[0]);
    expect(onChange.mock.calls.at(-1)?.[0].formData.file).toEqual([stored()]);
  });

  it('keeps new files when removing a stored reference from a mixed array', () => {
    const { onChange } = renderForm({ multiple: true, value: [stored(), raw] });
    fireEvent.click(screen.getAllByRole('button', { name: 'Remove' })[1]);
    expect(onChange.mock.calls.at(-1)?.[0].formData.file).toEqual([raw]);
  });

  it.each([false, true])(
    'supports uploading a replacement or appending to stored files (multiple=%s)',
    async (multiple) => {
      const { container, onChange } = renderForm({
        multiple,
        value: multiple ? [stored()] : stored(),
      });
      const input = container.querySelector('input[type=file]')!;
      fireEvent.change(input, {
        target: {
          files: [new File(['hello'], 'new.txt', { type: 'text/plain' })],
        },
      });
      await waitFor(() => expect(onChange).toHaveBeenCalled());
      expect(onChange.mock.calls.at(-1)?.[0].formData.file).toEqual(
        multiple ? [stored(), raw] : raw,
      );
    },
  );

  it('retains normal previews before submission', () => {
    renderForm({ value: raw });
    expect(screen.getByRole('link', { name: 'Preview' })).toHaveAttribute(
      'href',
      raw,
    );
  });
});
