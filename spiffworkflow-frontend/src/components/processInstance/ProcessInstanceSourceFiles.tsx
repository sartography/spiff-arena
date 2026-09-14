import { useEffect, useState } from 'react';
import { Alert, Box, CircularProgress, Stack } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { ModelSourceFile } from '../../interfaces';
import HttpService from '../../services/HttpService';
import ReactDiagramEditor from '../ReactDiagramEditor';
import DmnSourceViewer from './DmnSourceViewer';

type SourceResponse = {
  path: string;
  file_contents: string;
  encoding: 'utf-8' | 'base64';
  content_type: string;
};

function SourceContents({ file }: { file: SourceResponse }) {
  const { t } = useTranslation();
  const [downloadUrl, setDownloadUrl] = useState('');
  useEffect(() => {
    const contents =
      file.encoding === 'base64'
        ? Uint8Array.from(atob(file.file_contents), (character) =>
            character.charCodeAt(0),
          )
        : file.file_contents;
    const url = URL.createObjectURL(
      new Blob([contents], { type: file.content_type }),
    );
    setDownloadUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  let preview;
  if (file.path.endsWith('.dmn')) {
    preview = <DmnSourceViewer xml={file.file_contents} />;
  } else if (file.path.endsWith('.bpmn')) {
    preview = (
      <ReactDiagramEditor
        diagramType="readonly"
        diagramXML={file.file_contents}
        modifiedProcessModelId=""
      />
    );
  } else if (file.content_type.startsWith('image/')) {
    preview = (
      <img src={downloadUrl} alt={file.path} style={{ maxWidth: '100%' }} />
    );
  } else if (file.encoding === 'utf-8') {
    // Keep source templates/code inert, including Markdown, HTML and SVG source.
    preview = (
      <Box
        component="pre"
        sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}
      >
        {file.file_contents}
      </Box>
    );
  }
  return (
    <>
      <a href={downloadUrl} download={file.path.split('/').pop()}>
        {t('download_source_file')}
      </a>
      {preview}
    </>
  );
}

export default function ProcessInstanceSourceFiles({
  files,
  apiPath,
  selectedPath,
  onSelectPath,
}: {
  files: ModelSourceFile[];
  apiPath: string;
  selectedPath: string;
  onSelectPath: (path: string) => void;
}) {
  const { t } = useTranslation();
  const [result, setResult] = useState<{
    key: string;
    file?: SourceResponse;
    error?: string;
  } | null>(null);
  const path = files.some((file) => file.path === selectedPath)
    ? selectedPath
    : files[0]?.path || '';
  const key = `${apiPath}:${path}`;
  useEffect(() => {
    let active = true;
    if (path) {
      HttpService.makeCallToBackend({
        path: `${apiPath}/source-files?path=${encodeURIComponent(path)}`,
        successCallback: (file: SourceResponse) => {
          if (active) {
            setResult({ key, file });
          }
        },
        failureCallback: (error: Error) => {
          if (active) {
            setResult({ key, error: error.message });
          }
        },
        onUnauthorized: (error: Error) => {
          if (active) {
            setResult({ key, error: error.message });
          }
        },
      });
    }
    return () => {
      active = false;
    };
  }, [apiPath, key, path]);

  if (!files.length) {
    return <Alert severity="info">{t('historical_sources_unavailable')}</Alert>;
  }
  return (
    <Stack spacing={2} sx={{ mt: 2 }}>
      <label>
        {t('model_source_file')}{' '}
        <select
          value={path}
          onChange={(event) => onSelectPath(event.target.value)}
        >
          {files.map((file) => (
            <option key={file.path} value={file.path}>
              {file.path}
            </option>
          ))}
        </select>
      </label>
      {result?.key !== key ? (
        <CircularProgress size={24} />
      ) : (
        <>
          {result.error && <Alert severity="error">{result.error}</Alert>}
          {result.file && <SourceContents key={key} file={result.file} />}
        </>
      )}
    </Stack>
  );
}
