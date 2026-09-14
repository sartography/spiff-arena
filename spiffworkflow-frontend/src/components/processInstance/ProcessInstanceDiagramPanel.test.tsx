import { fireEvent, render, screen } from '@testing-library/react';
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
    default: ({ diagramXML, fileName, onElementClick }: any) => (
      <div
        data-testid="react-diagram-editor"
        data-diagram-xml={diagramXML}
        data-file-name={fileName}
      >
        <button
          type="button"
          onClick={() => onElementClick({ id: 'Rule' }, [])}
        >
          Inspect decision
        </button>
      </div>
    ),
  };
});

const baseProps = {
  tasks: [] as BasicTask[],
  tasksCallHadError: false,
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
        processInstance={testInstance({
          bpmn_xml_file_contents_retrieval_error:
            'Historical definition unavailable',
        })}
        {...baseProps}
      />,
    );
    expect(screen.getByText('failed_to_load_diagram')).toBeInTheDocument();
    expect(
      screen.queryByTestId('react-diagram-editor'),
    ).not.toBeInTheDocument();
  });

  it('shows an unavailable state even when the backend provides no error detail', () => {
    render(
      <ProcessInstanceDiagramPanel
        processInstance={testInstance()}
        {...baseProps}
      />,
    );
    expect(
      screen.queryByTestId('react-diagram-editor'),
    ).not.toBeInTheDocument();
    expect(
      screen.getAllByText('failed_to_load_diagram').length,
    ).toBeGreaterThan(0);
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
    expect(screen.getByTestId('react-diagram-editor')).not.toHaveAttribute(
      'data-file-name',
    );
  });
  it.each([
    '<businessRuleTask id="Rule" xmlns:s="http://spiffworkflow.org/bpmn/schema/1.0/core"><extensionElements><s:calledDecisionId>saved_decision</s:calledDecisionId></extensionElements></businessRuleTask>',
    '<businessRuleTask id="Rule" xmlns:c="http://camunda.org/schema/1.0/bpmn" c:decisionRef="saved_decision"/>',
  ])(
    'opens the archived decision referenced by a business-rule task: %s',
    (taskXml) => {
      const onDecisionNavigate = vi.fn(() => true);
      const onElementClick = vi.fn();
      render(
        <ProcessInstanceDiagramPanel
          {...baseProps}
          processInstance={testInstance({
            bpmn_xml_file_contents: `<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL">${taskXml}</definitions>`,
          })}
          onDecisionNavigate={onDecisionNavigate}
          onElementClick={onElementClick}
        />,
      );
      fireEvent.click(screen.getByRole('button', { name: 'Inspect decision' }));
      expect(onDecisionNavigate).toHaveBeenCalledWith('saved_decision');
      expect(onElementClick).not.toHaveBeenCalled();
    },
  );
});
