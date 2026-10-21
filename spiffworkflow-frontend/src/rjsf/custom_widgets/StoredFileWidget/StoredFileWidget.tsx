import { getDefaultRegistry } from '@rjsf/core';
import { getTemplate, WidgetProps } from '@rjsf/utils';
import { BACKEND_BASE_URL } from '../../../config';
import { modifyProcessIdentifierForPathParam } from '../../../helpers';

export type FileDownloadContext = {
  process_model_identifier: string;
  process_instance_id: number;
};

const DefaultFileWidget = getDefaultRegistry().widgets.FileWidget;

// These look like data URLs, but contain a database reference, NOT base64.
// Keep in sync with FILE_DATA_DIGEST_PREFIX and the reference format in the
// backend's process_instance_service.py.
// Passing them to RJSF produces corrupt previews and a fictitious file size.
const storedFile = (value: string) => {
  const match =
    /^data:([^;]*);name=(.*);base64,spifffiledatadigest\+([a-f0-9]{64})$/.exec(
      value,
    );
  if (!match) {
    return null;
  }
  let name = match[2];
  try {
    name = decodeURIComponent(name);
  } catch {
    // Older references stored literal filenames, including bare percent signs.
  }
  return { type: match[1], name, digest: match[3] };
};

export default function StoredFileWidget(props: WidgetProps) {
  const { value, multiple, onChange, disabled, readonly, registry, options } =
    props;
  const values: string[] = Array.isArray(value) ? value : value ? [value] : [];
  const stored = values.flatMap((item, index) => {
    const file = storedFile(item);
    return file ? [{ ...file, index }] : [];
  });
  if (!stored.length) {
    return <DefaultFileWidget {...props} />;
  }

  const rawValues = values.filter((item) => !storedFile(item));
  const context: FileDownloadContext | undefined =
    registry.formContext.fileDownloadContext;
  const { RemoveButton } = getTemplate('ButtonTemplates', registry, options);
  const handleChange: WidgetProps['onChange'] = (nextValue, errors, id) => {
    if (!multiple) {
      onChange(nextValue, errors, id);
      return;
    }
    const next: string[] = nextValue ?? [];
    // Preserve existing order when RJSF adds or removes a not-yet-saved file.
    onChange(
      [
        ...values.filter((item) => storedFile(item) || next.includes(item)),
        ...next.filter((item) => !rawValues.includes(item)),
      ],
      errors,
      id,
    );
  };

  return (
    <>
      {!disabled && !readonly && (
        <DefaultFileWidget
          {...props}
          value={multiple ? rawValues : undefined}
          required={false}
          onChange={handleChange}
        />
      )}
      <ul className="file-info">
        {stored.map((file) => {
          const href = context
            ? `${BACKEND_BASE_URL}/process-data-file-download/${modifyProcessIdentifierForPathParam(context.process_model_identifier)}/${context.process_instance_id}/${file.digest}`
            : undefined;
          return (
            <li key={file.index}>
              {href ? <a href={href}>{file.name}</a> : <span>{file.name}</span>}{' '}
              ({file.type})
              {!disabled && !readonly && (
                <RemoveButton
                  registry={registry}
                  onClick={() =>
                    onChange(
                      multiple
                        ? values.filter((_, index) => index !== file.index)
                        : undefined,
                    )
                  }
                />
              )}
            </li>
          );
        })}
      </ul>
    </>
  );
}
