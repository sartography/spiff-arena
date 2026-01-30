/**
 * BPMN-related utility functions extracted from the main application
 */

import { ReactElement } from 'react';
import { createRoot } from 'react-dom/client';
import { flushSync } from 'react-dom';

/**
 * Extract BPMN process identifiers from a root element
 * Recursively finds all process and subprocess IDs in the diagram
 */
export const getBpmnProcessIdentifiers = (rootBpmnElement: any): string[] => {
  const childProcesses = getChildProcesses(rootBpmnElement);
  childProcesses.push(rootBpmnElement.businessObject.id);
  return childProcesses;
};

/**
 * Get child processes from BPMN element (for diagram traversal)
 */
const getChildProcesses = (bpmnElement: any): string[] => {
  let childProcesses: string[] = [];
  bpmnElement.children.forEach((c: any) => {
    if (c.type === 'bpmn:Participant') {
      if (c.businessObject.processRef) {
        const childProcessesFromModdle = getChildProcessesFromModdleElement(
          c.businessObject.processRef,
        );
        childProcesses = childProcesses.concat(childProcessesFromModdle);
      }
    } else if (c.type === 'bpmn:SubProcess') {
      const childProcessesFromModdle = getChildProcessesFromModdleElement(
        c.businessObject,
      );
      childProcesses = childProcesses.concat(childProcessesFromModdle);
    }
  });
  return childProcesses;
};

/**
 * Get child processes from MODDLE element
 * Note: bpmn:SubProcess shape elements do not have children, they have flowElements
 */
const getChildProcessesFromModdleElement = (bpmnModdleElement: any): string[] => {
  let childProcesses: string[] = [bpmnModdleElement.id];
  bpmnModdleElement.flowElements.forEach((c: any) => {
    if (c.$type === 'bpmn:SubProcess') {
      const childProcessesFromModdle = getChildProcessesFromModdleElement(c);
      childProcesses = childProcesses.concat(childProcessesFromModdle);
    }
  });
  return childProcesses;
};

/**
 * Convert React SVG element to HTML string for overlays
 * Uses createRoot and flushSync to render React component to DOM
 */
export const convertSvgElementToHtmlString = (svgElement: ReactElement): string => {
  const div = document.createElement('div');
  const root = createRoot(div);
  flushSync(() => {
    root.render(svgElement);
  });
  const html = div.innerHTML;
  root.unmount();
  return html;
};

/**
 * Generate random ID for diagram elements
 */
export const makeid = (length: number): string => {
  let result = '';
  const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  const charactersLength = characters.length;
  let counter = 0;
  while (counter < length) {
    result += characters.charAt(Math.floor(Math.random() * charactersLength));
    counter += 1;
  }
  return result;
};

/**
 * Check if a task is a multi-instance child task
 */
export const taskIsMultiInstanceChild = (task: any): boolean => {
  return Object.hasOwn(task.runtime_info || {}, 'iteration');
};

/**
 * Check if a task can be highlighted in the diagram
 */
export const checkTaskCanBeHighlighted = (task: any): boolean => {
  const taskSpecsThatCannotBeHighlighted = ['Root', 'Start', 'End'];
  const taskBpmnId = task.bpmn_identifier;

  return (
    !taskIsMultiInstanceChild(task) &&
    !taskSpecsThatCannotBeHighlighted.includes(taskBpmnId) &&
    !taskBpmnId.match(/EndJoin/) &&
    !taskBpmnId.match(/BoundaryEventParent/) &&
    !taskBpmnId.match(/BoundaryEventJoin/) &&
    !taskBpmnId.match(/BoundaryEventSplit/)
  );
};