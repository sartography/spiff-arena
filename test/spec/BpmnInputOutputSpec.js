import {
  query as domQuery,
  queryAll as domQueryAll
} from 'min-dom';
import { bootstrapPropertiesPanel, CONTAINER } from './helpers';
import inputOutput from '../../app/spiffworkflow/InputOutput';
import { BpmnPropertiesPanelModule, BpmnPropertiesProviderModule } from 'bpmn-js-properties-panel';

describe('BPMN Input / Output', function() {

  let xml = require('./bpmn/diagram.bpmn').default;

  beforeEach(bootstrapPropertiesPanel(xml, {
    debounceInput: false,
    additionalModules: [
      inputOutput,
      BpmnPropertiesPanelModule,
      BpmnPropertiesProviderModule,
    ]
  }));

  it('should have a data input and data output in the properties panel', function() {
    var paletteElement = domQuery('.djs-palette', CONTAINER);
    var entries = domQueryAll('.entry', paletteElement);
    expect(entries[11].title).to.equals('Create DataInput');
    expect(entries[12].title).to.equals('Create DataOutput');
  });

});
