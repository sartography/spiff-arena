import DataObjectInterceptor from './DataObjectInterceptor';
import DataObjectRules from './DataObjectRules';
import RulesModule from 'diagram-js/lib/features/rules';
import DataObjectRenderer from './DataObjectRenderer';
import DataObjectPropertiesProvider from './propertiesPanel/DataObjectPropertiesProvider';
import DataObjectLabelEditingProvider from './DataObjectLabelEditingProvider';

export default {
  __depends__: [
    RulesModule
  ],
  __init__: [ 'dataInterceptor', 'dataObjectRules', 'dataObjectRenderer', 'dataObjectPropertiesProvider', 'dataObjectLabelEditingProvider' ],
  dataInterceptor: [ 'type', DataObjectInterceptor ],
  dataObjectRules: [ 'type', DataObjectRules ],
  dataObjectRenderer: [ 'type', DataObjectRenderer ],
  dataObjectPropertiesProvider: [ 'type', DataObjectPropertiesProvider ],
  dataObjectLabelEditingProvider: [ 'type', DataObjectLabelEditingProvider ]
};



