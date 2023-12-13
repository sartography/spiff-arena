import { is } from 'bpmn-js/lib/util/ModelUtil';
import { DataStoreSelect, OPTION_TYPE } from './DataStoreSelect';

const LOW_PRIORITY = 500;

export default function DataStorePropertiesProvider(
  modeling,
  propertiesPanel,
  translate,
  moddle,
  commandStack,
  bpmnFactory,
) {
  this.getGroups = function (element) {
    return function (groups) {
      if (is(element, 'bpmn:DataStoreReference')) {
        groups.push(
          createCustomDataStoreGroup(
            modeling,
            element,
            translate,
            moddle,
            commandStack,
            bpmnFactory
          )
        );
      }
      return groups;
    };
  };
  propertiesPanel.registerProvider(LOW_PRIORITY, this);
}

DataStorePropertiesProvider.$inject = [
  'modeling',
  'propertiesPanel',
  'translate',
  'moddle',
  'commandStack',
  'bpmnFactory',
];

function createCustomDataStoreGroup(
  modeling,
  element,
  translate,
  moddle,
  commandStack,
  bpmnFactory
) {
  const group = {
    label: translate('Custom Data Store Properties'),
    id: 'custom-datastore-properties',
    entries: [],
  };

  // other custom properties as needed
  group.entries.push({
    id: 'selectDataStore',
    element,
    component: DataStoreSelect,
    optionType: OPTION_TYPE.data_stores,
    moddle,
    commandStack,
    translate,
    name: 'dataStoreRef',
    label: translate('Select DataSource'),
    description: translate('Select a datasource from the list'),
    modeling,
    bpmnFactory,
  });

  return group;
}
