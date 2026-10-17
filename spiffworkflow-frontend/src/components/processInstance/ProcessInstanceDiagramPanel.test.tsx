import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { BasicTask, ProcessInstanceDiagram } from '../../interfaces';
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

const testDiagram = (
  overrides: Partial<ProcessInstanceDiagram> = {},
): ProcessInstanceDiagram => ({
  bpmn_xml_file_contents: null,
  bpmn_xml_file_contents_retrieval_error: null,
  process_model_with_diagram_identifier: null,
  ...overrides,
});

describe('ProcessInstanceDiagramPanel', () => {
  it('shows a loading indicator while the diagram loads', () => {
    render(<ProcessInstanceDiagramPanel diagram={null} {...baseProps} />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('shows a loading indicator while tasks load', () => {
    render(
      <ProcessInstanceDiagramPanel
        diagram={testDiagram()}
        {...baseProps}
        tasks={null}
      />,
    );
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('shows an error when the diagram cannot be loaded', () => {
    render(
      <ProcessInstanceDiagramPanel
        diagram={testDiagram()}
        {...baseProps}
        diagramLoadError="boom"
      />,
    );
    expect(screen.getByText('failed_to_load_diagram')).toBeInTheDocument();
  });

  it('renders the diagram editor with inline xml', () => {
    render(
      <ProcessInstanceDiagramPanel
        diagram={testDiagram({ bpmn_xml_file_contents: '<xml/>' })}
        {...baseProps}
      />,
    );
    expect(screen.getByTestId('react-diagram-editor')).toHaveAttribute(
      'data-diagram-xml',
      '<xml/>',
    );
  });
});
