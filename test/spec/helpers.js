import { query as domQuery } from 'min-dom';
import { act, fireEvent } from '@testing-library/preact';

import {
  getBpmnJS,
  bootstrapBpmnJS,
  inject,
  insertCSS,
} from 'bpmn-js/test/helper';
import Modeler from 'bpmn-js/lib/Modeler';
import TestContainer from 'mocha-test-container-support';
import { getBusinessObject } from 'bpmn-js/lib/util/ModelUtil';
import { createMoveEvent } from 'diagram-js/lib/features/mouse/Mouse';

export let PROPERTIES_PANEL_CONTAINER;
export let CONTAINER;

export function bootstrapPropertiesPanel(diagram, options, locals) {
  return async function () {
    let { container } = options;
    if (!container) {
      container = TestContainer.get(this);
    }
    CONTAINER = container;

    insertBpmnStyles();
    insertCoreStyles();
    const createModeler = bootstrapBpmnJS(Modeler, diagram, options, locals);
    await act(() => createModeler.call(this));

    // (2) clean-up properties panel
    clearPropertiesPanelContainer();

    // (3) attach properties panel
    const attachPropertiesPanel = inject(function (propertiesPanel) {
      PROPERTIES_PANEL_CONTAINER = document.createElement('div');
      PROPERTIES_PANEL_CONTAINER.classList.add('properties-container');

      container.appendChild(PROPERTIES_PANEL_CONTAINER);

      return act(() => propertiesPanel.attachTo(PROPERTIES_PANEL_CONTAINER));
    });
    await attachPropertiesPanel();
  };
}

export function clearPropertiesPanelContainer() {
  if (PROPERTIES_PANEL_CONTAINER) {
    PROPERTIES_PANEL_CONTAINER.remove();
  }
}

export function insertCoreStyles() {
  insertCSS(
    'properties-panel.css',
    require('bpmn-js-properties-panel/dist/assets/properties-panel.css').default
  );
  insertCSS('test.css', require('./test.css').default);
}

export function insertBpmnStyles() {
  insertCSS(
    'diagram.css',
    require('bpmn-js/dist/assets/diagram-js.css').default
  );

  // @barmac: this fails before bpmn-js@9
  insertCSS('bpmn-js.css', require('bpmn-js/dist/assets/bpmn-js.css').default);

  insertCSS(
    'bpmn-font.css',
    require('bpmn-js/dist/assets/bpmn-font/css/bpmn-embedded.css').default
  );
}

export function expectSelected(id) {
  return getBpmnJS().invoke(async function (elementRegistry, selection) {
    const element = elementRegistry.get(id);

    await act(() => {
      selection.select(element);
    });

    return element;
  });
}

export function getPropertiesPanel() {
  return PROPERTIES_PANEL_CONTAINER;
}

export function findEntry(id, container) {
  return domQuery(`[data-entry-id='${id}']`, container);
}

export function findGroupEntry(id, container) {
  return domQuery(`[data-group-id='group-${id}']`, container);
}

export function findInput(type, container) {
  return domQuery(`input[type='${type}']`, container);
}

export function findTextarea(id, container) {
  return domQuery(`textarea[id='${id}']`, container);
}

export function findButton(id, container) {
  return domQuery(`button[id='${id}']`, container);
}

export function findButtonByClass(buttonClass, container) {
  return domQuery(`button[class='${buttonClass}']`, container);
}

export function findSelect(container) {
  return domQuery('select', container);
}

export function changeInput(input, value) {
  fireEvent.input(input, { target: { value } });
}

export function pressButton(button) {
  fireEvent.click(button);
}

export function findDivByClass(divClass, container) {
  return domQuery(`div[class='${divClass}']`, container);
}

/**
 * Drags an element from the palette onto the canvas.
 * @param id
 */
export function triggerPaletteEntry(id) {
  getBpmnJS().invoke(function (palette) {
    const entry = palette.getEntries()[id];

    if (entry && entry.action && entry.action.click) {
      entry.action.click(createMoveEvent(0, 0));
    }
  });
}
