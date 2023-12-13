import RulesModule from 'diagram-js/lib/features/rules';
import DataStorePropertiesProvider from './propertiesPanel/DataStorePropertiesProvider';
import DataStoreInterceptor from './DataStoreInterceptor';

export default {
  __depends__: [
    RulesModule
  ],
  __init__: [ 'dataStoreInterceptor', 'dataStorePropertiesProvider' ],
  dataStoreInterceptor: [ 'type', DataStoreInterceptor ],
  dataStorePropertiesProvider: [ 'type', DataStorePropertiesProvider ]
};
