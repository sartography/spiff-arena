import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { BasicTask, ProcessInstance } from '../../interfaces';
import ProcessInstanceDiagramPanel from './ProcessInstanceDiagramPanel';

vi.mock('react-i18next', () => {
  return {
    useTranslation: () => ({
      t: (value: string) => value,
    }),
  };
});

vi.mock('../ReactDiagramEditor', () => {
  return {
    default: ({ diagramXML, fileName }: any) => (
      <div
        data-testid="react-diagram-editor"
        data-diagram-xml={diagramXML}
        data-file-name={fileName}
      />
    ),
  };
});

const baseProps = {
  tasks: [] as BasicTask[],
  tasksCallHadError: false,
  diagramFileName: null,
  diagramProcessModelId: null,
  diagramLoadError: null,
  modifiedProcessModelId: 'test/model',
  onCallActivityNavigate: vi.fn(),
  onElementClick: vi.fn(),
};

const testInstance = (overrides: Partial<ProcessInstance> = {}) =>
  ({
    id: 42,
    status: 'waiting',
    ...overrides,
  }) as ProcessInstance;

describe('ProcessInstanceDiagramPanel', () => {
  it('renders nothing without a process instance', () => {
    const { container } = render(
      <ProcessInstanceDiagramPanel processInstance={null} {...baseProps} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('shows a loading indicator while tasks and the diagram load', () => {
    render(
      <ProcessInstanceDiagramPanel
        processInstance={testInstance()}
        {...baseProps}
        tasks={null}
      />,
    );
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('shows an error when the diagram cannot be loaded', () => {
    render(
      <ProcessInstanceDiagramPanel
        processInstance={testInstance()}
        {...baseProps}
        diagramLoadError="boom"
      />,
    );
    expect(screen.getByText('failed_to_load_diagram')).toBeInTheDocument();
  });

  it('renders the diagram editor with inline xml', () => {
    render(
      <ProcessInstanceDiagramPanel
        processInstance={testInstance({ bpmn_xml_file_contents: '<xml/>' })}
        {...baseProps}
      />,
    );
    expect(screen.getByTestId('react-diagram-editor')).toHaveAttribute(
      'data-diagram-xml',
      '<xml/>',
    );
  });
});
