import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import HttpService from '../../services/HttpService';
import ProcessInstanceSourceFiles from './ProcessInstanceSourceFiles';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));
vi.mock('../../services/HttpService', () => ({
  default: { makeCallToBackend: vi.fn() },
}));
vi.mock('./DmnSourceViewer', () => ({
  default: ({ xml }: { xml: string }) => (
    <div data-testid="saved-decision">{xml}</div>
  ),
}));
vi.mock('../ReactDiagramEditor', () => ({
  default: ({ diagramType, diagramXML }: any) => (
    <div data-testid="saved-bpmn" data-mode={diagramType}>
      {diagramXML}
    </div>
  ),
}));

const files = ['decision.dmn', 'form.json', 'main.bpmn'].map((name) => ({
  path: `group/model/${name}`,
  digest: name,
  content_type: 'application/xml',
  size: 12,
}));
const apiPath = '/process-instances/for-me/group:model/42';

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubGlobal(
    'URL',
    class extends URL {
      static readonly createObjectURL = vi.fn(() => 'blob:saved-source');
      static readonly revokeObjectURL = vi.fn();
    },
  );
});

describe('ProcessInstanceSourceFiles', () => {
  it('loads DMN only through the instance source endpoint', async () => {
    vi.mocked(HttpService.makeCallToBackend).mockImplementation(
      ({ successCallback }) => {
        successCallback({
          path: files[0].path,
          file_contents: '<decision>Old table</decision>',
          encoding: 'utf-8',
          content_type: 'application/xml',
        });
      },
    );
    render(
      <ProcessInstanceSourceFiles
        files={files}
        apiPath={apiPath}
        selectedPath={files[0].path}
        onSelectPath={vi.fn()}
      />,
    );
    expect(await screen.findByTestId('saved-decision')).toHaveTextContent(
      'Old table',
    );
    expect(HttpService.makeCallToBackend).toHaveBeenCalledWith(
      expect.objectContaining({
        path: `${apiPath}/source-files?path=group%2Fmodel%2Fdecision.dmn`,
      }),
    );
    expect(screen.getByRole('link')).toHaveAttribute(
      'download',
      'decision.dmn',
    );
  });

  it('discards an old response when the selected file changes', async () => {
    const responses: Function[] = [];
    vi.mocked(HttpService.makeCallToBackend).mockImplementation(
      ({ successCallback }) => {
        responses.push(successCallback);
      },
    );
    const props = { files, apiPath, onSelectPath: vi.fn() };
    const { rerender } = render(
      <ProcessInstanceSourceFiles {...props} selectedPath={files[0].path} />,
    );
    rerender(
      <ProcessInstanceSourceFiles {...props} selectedPath={files[1].path} />,
    );
    responses[1]({
      path: files[1].path,
      file_contents: '{"title":"Saved form"}',
      encoding: 'utf-8',
      content_type: 'application/json',
    });
    expect(
      await screen.findByText('{"title":"Saved form"}'),
    ).toBeInTheDocument();
    responses[0]({
      path: files[0].path,
      file_contents: 'Stale decision',
      encoding: 'utf-8',
      content_type: 'application/xml',
    });
    await waitFor(() =>
      expect(screen.queryByText('Stale decision')).not.toBeInTheDocument(),
    );
    fireEvent.change(screen.getByRole('combobox'), {
      target: { value: files[2].path },
    });
    expect(props.onSelectPath).toHaveBeenCalledWith(files[2].path);
  });

  it('shows a historical-file error without requesting current model files', async () => {
    vi.mocked(HttpService.makeCallToBackend).mockImplementation(
      ({ failureCallback }) => {
        failureCallback?.({ message: 'Historical file unavailable' });
      },
    );
    render(
      <ProcessInstanceSourceFiles
        files={files}
        apiPath={apiPath}
        selectedPath={files[0].path}
        onSelectPath={vi.fn()}
      />,
    );
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Historical file unavailable',
    );
    expect(HttpService.makeCallToBackend).toHaveBeenCalledTimes(1);
    expect(screen.queryByTestId('saved-decision')).not.toBeInTheDocument();
  });

  it('keeps archived BPMN read-only', async () => {
    vi.mocked(HttpService.makeCallToBackend).mockImplementation(
      ({ successCallback }) => {
        successCallback({
          path: files[2].path,
          file_contents: '<process/>',
          encoding: 'utf-8',
          content_type: 'application/xml',
        });
      },
    );
    render(
      <ProcessInstanceSourceFiles
        files={files}
        apiPath={apiPath}
        selectedPath={files[2].path}
        onSelectPath={vi.fn()}
      />,
    );
    expect(await screen.findByTestId('saved-bpmn')).toHaveAttribute(
      'data-mode',
      'readonly',
    );
  });
});
