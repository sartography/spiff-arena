import { assign } from 'min-dash';
import translate from 'diagram-js/lib/i18n/translate/translate';

/**
 * Add data inputs and data outputs to the panel.
 */
export default function IoPalette(palette, create, elementFactory,) {
  this._create = create;
  this._elementFactory = elementFactory;
  palette.registerProvider(this);
}

IoPalette.$inject = [
  'palette',
  'create',
  'elementFactory'
];

IoPalette.prototype.getPaletteEntries = function() {

  let input_type = 'bpmn:DataInput';
  let output_type = 'bpmn:DataOutput';
  let elementFactory = this._elementFactory, create = this._create;

  function createListener(event, type) {
    let shape = elementFactory.createShape(assign({ type: type }, {}));
    shape.width = 36; // Fix up the shape dimensions from the defaults.
    shape.height = 50;
    create.start(event, shape);
  }

  function createInputListener(event) {
    createListener(event, input_type);
  }

  function createOutputListener(event) {
    createListener(event, output_type);
  }

  return {
    'create.data-input': {
      group: 'data-object',
      className: 'bpmn-icon-data-input',
      title: translate('Create DataInput'),
      action: {
        dragstart: createInputListener,
        click: createInputListener
      }
    },
    'create.data-output': {
      group: 'data-object',
      className: 'bpmn-icon-data-output',
      title: translate('Create DataOutput'),
      action: {
        dragstart: createOutputListener,
        click: createOutputListener
      }
    }

  };
};

