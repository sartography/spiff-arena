import { ChangeEvent, useCallback, useMemo } from 'react';
import {
  ariaDescribedByIds,
  dataURItoBlob,
  examplesId,
  FormContextType,
  getInputProps,
  getTemplate,
  Registry,
  RJSFSchema,
  StrictRJSFSchema,
  TranslatableString,
  UIOptionsType,
  WidgetProps,
} from '@rjsf/utils';
import Markdown from 'markdown-to-jsx';
import { FileUploader } from '@carbon/react';
import { getCommonAttributes } from '../../helpers';

function addNameToDataURL(dataURL: string, name: string) {
  if (dataURL === null) {
    return null;
  }
  return dataURL.replace(';base64', `;name=${encodeURIComponent(name)};base64`);
}

type FileInfoType = {
  dataURL?: string | null;
  name: string;
  size: number;
  type: string;
};

function processFile(file: File): Promise<FileInfoType> {
  const { name, size, type } = file;
  return new Promise((resolve, reject) => {
    const reader = new window.FileReader();
    reader.onerror = reject;
    reader.onload = (event) => {
      if (typeof event.target?.result === 'string') {
        resolve({
          dataURL: addNameToDataURL(event.target.result, name),
          name,
          size,
          type,
        });
      } else {
        resolve({
          dataURL: null,
          name,
          size,
          type,
        });
      }
    };
    reader.readAsDataURL(file);
  });
}

function processFiles(files: FileList) {
  return Promise.all(Array.from(files).map(processFile));
}

function FileInfoPreview<
  T = any,
  S extends StrictRJSFSchema = RJSFSchema,
  F extends FormContextType = any,
>({
  fileInfo,
  registry,
}: {
  fileInfo: FileInfoType;
  registry: Registry<T, S, F>;
}) {
  const { translateString } = registry;
  const { dataURL, type, name } = fileInfo;
  if (!dataURL) {
    return null;
  }

  // If type is JPEG or PNG then show image preview.
  // Originally, any type of image was supported, but this was changed into a whitelist
  // since SVGs and animated GIFs are also images, which are generally considered a security risk.
  if (['image/jpeg', 'image/png'].includes(type)) {
    return (
      <img
        src={dataURL}
        style={{ maxWidth: '100%' }}
        className="file-preview"
      />
    );
  }

  // otherwise, let users download file

  return (
    <>
      {' '}
      <a download={`preview-${name}`} href={dataURL} className="file-download">
        {translateString(TranslatableString.PreviewLabel)}
      </a>
    </>
  );
}

function FilesInfo<
  T = any,
  S extends StrictRJSFSchema = RJSFSchema,
  F extends FormContextType = any,
>({
  filesInfo,
  registry,
  preview,
  onRemove,
  options,
}: {
  filesInfo: FileInfoType[];
  registry: Registry<T, S, F>;
  preview?: boolean;
  onRemove: (index: number) => void;
  options: UIOptionsType<T, S, F>;
}) {
  if (filesInfo.length === 0) {
    return null;
  }
  const { translateString } = registry;

  // MuiRemoveButton doesn't exist on the correct component type but we add that manually so we know it is there
  const { MuiRemoveButton } = getTemplate<any, any, any>(
    'ButtonTemplates',
    registry,
    options as UIOptionsType<any, any, any>,
  );

  return (
    <ul className="file-info">
      {filesInfo.map((fileInfo, key) => {
        const { name, size, type } = fileInfo;
        const handleRemove = () => onRemove(key);
        return (
          <li key={key}>
            <Markdown>
              {translateString(TranslatableString.FilesInfo, [
                name,
                type,
                String(size),
              ])}
            </Markdown>
            {preview && (
              <FileInfoPreview<T, S, F>
                fileInfo={fileInfo}
                registry={registry}
              />
            )}
            <MuiRemoveButton onClick={handleRemove} registry={registry} />
          </li>
        );
      })}
    </ul>
  );
}

function extractFileInfo(dataURLs: string[]): FileInfoType[] {
  return dataURLs.reduce((acc, dataURL) => {
    if (!dataURL) {
      return acc;
    }
    try {
      const { blob, name } = dataURItoBlob(dataURL);
      return [
        ...acc,
        {
          dataURL,
          name: name,
          size: blob.size,
          type: blob.type,
        },
      ];
    } catch (e) {
      // Invalid dataURI, so just ignore it.
      return acc;
    }
  }, [] as FileInfoType[]);
}

/**
 *  The `FileWidget` is a widget for rendering file upload fields.
 *  It is typically used with a string property with data-url format.
 */
function FileWidget<
  T = any,
  S extends StrictRJSFSchema = RJSFSchema,
  F extends FormContextType = any,
>(props: WidgetProps<T, S, F>) {
  const {
    autofocus,
    disabled,
    id,
    label,
    multiple,
    onBlur,
    onChange,
    onFocus,
    options,
    rawErrors,
    readonly,
    registry,
    required,
    schema,
    type,
    uiSchema,
    value,
    ...rest
  } = props;
  const BaseInputTemplate = getTemplate<'BaseInputTemplate', T, S, F>(
    'BaseInputTemplate',
    registry,
    options,
  );

  const handleChange = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      if (!event.target.files) {
        return;
      }
      // Due to variances in themes, dealing with multiple files for the array case now happens one file at a time.
      // This is because we don't pass `multiple` into the `BaseInputTemplate` anymore. Instead, we deal with the single
      // file in each event and concatenate them together ourselves
      processFiles(event.target.files).then((filesInfoEvent) => {
        const newValue = filesInfoEvent.map((fileInfo) => fileInfo.dataURL);
        if (multiple) {
          onChange(value.concat(newValue[0]));
        } else {
          onChange(newValue[0]);
        }
      });
    },
    [multiple, value, onChange],
  );

  const _onBlur = useCallback(
    ({ target }: React.FocusEvent<HTMLInputElement>) =>
      onBlur(id, target.value),
    [onBlur, id],
  );
  const _onFocus = useCallback(
    ({ target }: React.FocusEvent<HTMLInputElement>) =>
      onFocus(id, target.value),
    [onFocus, id],
  );

  const commonAttributes = getCommonAttributes(
    label,
    schema,
    uiSchema,
    rawErrors,
  );

  const filesInfo = useMemo(
    () => extractFileInfo(Array.isArray(value) ? value : [value]),
    [value],
  );
  const rmFile = useCallback(
    (index: number) => {
      if (multiple) {
        const newValue = value.filter((_: any, i: number) => i !== index);
        onChange(newValue);
      } else {
        onChange(undefined);
      }
    },
    [multiple, value, onChange],
  );

  const inputProps = {
    ...rest,
    ...getInputProps<T, S, F>(schema, type, options),
  };

  let inputValue;
  if (inputProps.type === 'number' || inputProps.type === 'integer') {
    inputValue = value || value === 0 ? value : '';
  } else {
    inputValue = value == null ? '' : value;
  }

  let wrapperProps = null;
  let errorSvg = null;
  if (commonAttributes.invalid) {
    wrapperProps = { 'data-invalid': true };
    errorSvg = (
      <svg
        focusable="false"
        preserveAspectRatio="xMidYMid meet"
        fill="currentColor"
        width="16"
        height="16"
        viewBox="0 0 16 16"
        aria-hidden="true"
        xmlns="http://www.w3.org/2000/svg"
        className="cds--text-input__invalid-icon"
      >
        <path d="M8,1C4.2,1,1,4.2,1,8s3.2,7,7,7s7-3.1,7-7S11.9,1,8,1z M7.5,4h1v5h-1C7.5,9,7.5,4,7.5,4z M8,12.2 c-0.4,0-0.8-0.4-0.8-0.8s0.3-0.8,0.8-0.8c0.4,0,0.8,0.4,0.8,0.8S8.4,12.2,8,12.2z"></path>
        <path
          d="M7.5,4h1v5h-1C7.5,9,7.5,4,7.5,4z M8,12.2c-0.4,0-0.8-0.4-0.8-0.8s0.3-0.8,0.8-0.8 c0.4,0,0.8,0.4,0.8,0.8S8.4,12.2,8,12.2z"
          data-icon-path="inner-path"
          opacity="0"
        ></path>
      </svg>
    );
  }

  return (
    <>
      <div className="cds--text-input__field-wrapper" {...wrapperProps}>
        {errorSvg}
        <input
          {...inputProps}
          className="file-upload"
          readOnly={readonly}
          disabled={disabled}
          id={id}
          name={id}
          value={inputValue}
          list={schema.examples ? examplesId<T>(id) : undefined}
          onChange={handleChange}
          aria-describedby={ariaDescribedByIds<T>(id, !!schema.examples)}
          type="file"
          accept={options.accept ? String(options.accept) : undefined}
          autoFocus={autofocus}
          onBlur={_onBlur}
          onFocus={_onFocus}
        />

        <span role="alert" className="cds--text-input__counter-alert"></span>
      </div>
      <FilesInfo<T, S, F>
        filesInfo={filesInfo}
        onRemove={rmFile}
        registry={registry}
        preview={options.filePreview}
        options={options}
      />
      <div id={`${id}-error-msg`} className="cds--form-requirement">
        {commonAttributes.errorMessageForField}
      </div>
    </>
  );
}

export default FileWidget;
