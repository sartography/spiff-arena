import BaseRenderer from 'diagram-js/lib/draw/BaseRenderer';

import {
  attr as svgAttr
} from 'tiny-svg';

import { getBusinessObject, is } from 'bpmn-js/lib/util/ModelUtil';
import { isAny } from 'bpmn-js/lib/features/modeling/util/ModelingUtil';
import { findDataObject } from './DataObjectHelpers';

const HIGH_PRIORITY = 1500;

/**
 * Work in progress -- render data object references in red if they are
 * not valid.
 */
export default class DataObjectRenderer extends BaseRenderer {
  constructor(eventBus, bpmnRenderer) {
    super(eventBus, HIGH_PRIORITY);
    this.bpmnRenderer = bpmnRenderer;
  }

  canRender(element) {
    return isAny(element, [ 'bpmn:DataObjectReference' ]) && !element.labelTarget;
  }

  drawShape(parentNode, element) {
    const shape = this.bpmnRenderer.drawShape(parentNode, element);
    if (is(element, 'bpmn:DataObjectReference')) {
      let businessObject = getBusinessObject(element);
      let dataObject = businessObject.dataObjectRef;
      if (dataObject && dataObject.id) {
        let parentObject = businessObject.$parent;
        dataObject = findDataObject(parentObject, dataObject.id);
      }
      if (!dataObject) {
        svgAttr(shape, 'stroke', 'red');
      }
      return shape;
    }
  }
}

DataObjectRenderer.$inject = [ 'eventBus', 'bpmnRenderer' ];
