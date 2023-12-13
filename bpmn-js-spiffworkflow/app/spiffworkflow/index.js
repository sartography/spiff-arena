import RulesModule from 'diagram-js/lib/features/rules';
import IoPalette from './InputOutput/IoPalette';
import IoRules from './InputOutput/IoRules';
import IoInterceptor from './InputOutput/IoInterceptor';
import DataObjectInterceptor from './DataObject/DataObjectInterceptor';
import DataObjectRules from './DataObject/DataObjectRules';
import DataObjectRenderer from './DataObject/DataObjectRenderer';
import DataObjectPropertiesProvider from './DataObject/propertiesPanel/DataObjectPropertiesProvider';
import DataObjectLabelEditingProvider from './DataObject/DataObjectLabelEditingProvider';
import DataStorePropertiesProvider from './DataStoreReference/propertiesPanel/DataStorePropertiesProvider';
import DataStoreInterceptor from './DataStoreReference/DataStoreInterceptor';
import ConditionsPropertiesProvider from './conditions/propertiesPanel/ConditionsPropertiesProvider';
import ExtensionsPropertiesProvider from './extensions/propertiesPanel/ExtensionsPropertiesProvider';
import MessagesPropertiesProvider from './messages/propertiesPanel/MessagesPropertiesProvider';
import SignalPropertiesProvider from './signals/propertiesPanel/SignalPropertiesProvider';
import ErrorPropertiesProvider from './errors/propertiesPanel/ErrorPropertiesProvider';
import EscalationPropertiesProvider from './escalations/propertiesPanel/EscalationPropertiesProvider';
import CallActivityPropertiesProvider from './callActivity/propertiesPanel/CallActivityPropertiesProvider';
import StandardLoopPropertiesProvider from './loops/propertiesPanel/StandardLoopPropertiesProvider';
import MultiInstancePropertiesProvider from './loops/propertiesPanel/MultiInstancePropertiesProvider';

export default {
  __depends__: [RulesModule],
  __init__: [
    'dataObjectInterceptor',
    'dataObjectRules',
    'dataObjectPropertiesProvider',
    'dataObjectLabelEditingProvider',
    'dataStoreInterceptor',
    'dataStorePropertiesProvider',
    'conditionsPropertiesProvider',
    'extensionsPropertiesProvider',
    'messagesPropertiesProvider',
    'signalPropertiesProvider',
    'errorPropertiesProvider',
    'escalationPropertiesProvider',
    'callActivityPropertiesProvider',
    'ioPalette',
    'ioRules',
    'ioInterceptor',
    'dataObjectRenderer',
    'multiInstancePropertiesProvider',
    'standardLoopPropertiesProvider',
  ],
  dataObjectInterceptor: ['type', DataObjectInterceptor],
  dataObjectRules: ['type', DataObjectRules],
  dataObjectRenderer: ['type', DataObjectRenderer],
  dataObjectPropertiesProvider: ['type', DataObjectPropertiesProvider],
  dataObjectLabelEditingProvider: ['type', DataObjectLabelEditingProvider],
  dataStoreInterceptor: ['type', DataStoreInterceptor],
  dataStorePropertiesProvider: ['type', DataStorePropertiesProvider],
  conditionsPropertiesProvider: ['type', ConditionsPropertiesProvider],
  extensionsPropertiesProvider: ['type', ExtensionsPropertiesProvider],
  signalPropertiesProvider: ['type', SignalPropertiesProvider],
  errorPropertiesProvider: ['type', ErrorPropertiesProvider],
  escalationPropertiesProvider: ['type', EscalationPropertiesProvider],
  messagesPropertiesProvider: ['type', MessagesPropertiesProvider],
  callActivityPropertiesProvider: ['type', CallActivityPropertiesProvider],
  ioPalette: ['type', IoPalette],
  ioRules: ['type', IoRules],
  ioInterceptor: ['type', IoInterceptor],
  multiInstancePropertiesProvider: ['type', MultiInstancePropertiesProvider],
  standardLoopPropertiesProvider: ['type', StandardLoopPropertiesProvider],
};
