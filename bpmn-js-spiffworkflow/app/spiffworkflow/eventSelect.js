import { is, isAny } from 'bpmn-js/lib/util/ModelUtil';
import { useService } from 'bpmn-js-properties-panel';
import {
  ListGroup,
  TextFieldEntry,
  TextAreaEntry,
  SelectEntry,
  isTextFieldEntryEdited
} from '@bpmn-io/properties-panel';
import { getRoot } from './helpers';

function hasEventType(element, eventType) {
  const events = element.businessObject.eventDefinitions;
  return events && events.filter(item => is(item, eventType)).length > 0;
}

function replaceGroup(groupId, groups, group) {
  const idx = groups.map(g => g.id).indexOf(groupId);
  if (idx > -1)
    groups.splice(idx, 1, group);
  else
    groups.push(group);
  group.shouldOpen = true;
}

function isCatchingEvent(element) {
  return isAny(element, ['bpmn:StartEvent', 'bpmn:IntermediateCatchEvent', 'bpmn:BoundaryEvent']);
}

function isThrowingEvent(element) {
  return isAny(element, ['bpmn:EndEvent', 'bpmn:IntermediateThrowEvent']);
}

function getConfigureGroupForType(eventDetails, label, includeCode, getSelect) {

  const { eventType, eventDefType, referenceType, idPrefix } = eventDetails;

  return function (props) {
    const { element, translate, moddle, commandStack } = props;

    const variableName = getTextFieldForExtension(eventDetails, 'Variable Name', 'The name of the variable to store the payload in', true);
    const payloadDefinition = getTextFieldForExtension(eventDetails, 'Payload', 'The expression to create the payload with', false);

    const entries = [
      {
        id: `${idPrefix}-select`,
        element,
        component: getSelect,
        isEdited: isTextFieldEntryEdited,
        moddle,
        commandStack,
      },
    ];

    if (includeCode) {
      const codeField = getCodeTextField(eventDetails, `${label} Code`);
      entries.push({
        id: `${idPrefix}-code`,
        element,
        component: codeField,
        isEdited: isTextFieldEntryEdited,
        moddle,
        commandStack,
      });
    }


    if (isCatchingEvent(element)) {
      entries.push({
        id: `${idPrefix}-variable`,
        element,
        component: variableName,
        isEdited: isTextFieldEntryEdited,
        moddle,
        commandStack,
      });
    } else if (isThrowingEvent(element)) {
      entries.push({
        id: `${idPrefix}-payload`,
        element,
        component: payloadDefinition,
        isEdited: isTextFieldEntryEdited,
        moddle,
        commandStack,
      });
    };
    return {
      id: `${idPrefix}-group`,
      label: label,
      entries,
    }
  }
}

function getSelectorForType(eventDetails) {

  const { eventType, eventDefType, referenceType, idPrefix } = eventDetails;

  return function (props) {
    const { element, translate, moddle, commandStack } = props;
    const debounce = useService('debounceInput');
    const root = getRoot(element.businessObject);

    const getValue = () => {
      const eventDef = element.businessObject.eventDefinitions.find(v => v.$type == eventDefType);
      return (eventDef && eventDef.get(referenceType)) ? eventDef.get(referenceType).id : '';
    };

    const setValue = (value) => {
      const bpmnEvent = root.rootElements.find(e => e.id == value);
      // not sure how to handle multiple event definitions
      const eventDef = element.businessObject.eventDefinitions.find(v => v.$type == eventDefType);
      // really not sure what to do here if one of these can't be found either
      if (bpmnEvent && eventDef)
        eventDef.set(referenceType, bpmnEvent);
      commandStack.execute('element.updateProperties', {
        element,
        moddleElement: element.businessObject,
        properties: {},
      });
    };

    const getOptions = (val) => {
      const matching = root.rootElements ? root.rootElements.filter(elem => elem.$type === eventType) : [];
      const options = [];
      matching.map(option => options.push({label: option.name, value: option.id}));
      return options;
    }

    return SelectEntry({
      id: `${idPrefix}-select`,
      element,
      description: 'Select item',
      getValue,
      setValue,
      getOptions,
      debounce,
    });
  }
}

function getTextFieldForExtension(eventDetails, label, description, catching) {

  const { eventType, eventDefType, referenceType, idPrefix } = eventDetails;

  return function (props) {
    const { element, moddle, commandStack } = props;
    const debounce = useService('debounceInput');
    const translate = useService('translate');
    const root = getRoot(element.businessObject);
    const extensionName = (catching) ? 'spiffworkflow:variableName' : 'spiffworkflow:payloadExpression';

    const getEvent = () => {
      const eventDef = element.businessObject.eventDefinitions.find(v => v.$type == eventDefType);
      const bpmnEvent = eventDef.get(referenceType);
      return bpmnEvent;
    };

    const getValue = () => {
      // I've put the variable name (and payload) on the event for consistency with messages.
      // However, when I think about this, I wonder if it shouldn't be on the event definition.
      // I think that's something we should address in the future.
      // Creating a payload and defining access to it are both process-specific, and that's an argument for leaving
      // it in the event definition
      const bpmnEvent = getEvent();
      if (bpmnEvent && bpmnEvent.extensionElements) {
        const extension = bpmnEvent.extensionElements.get('values').find(ext => ext.$instanceOf(extensionName));
        return (extension) ? extension.value : null;
      }
    }

    const setValue = (value)  => {
      const bpmnEvent = getEvent();
      if (bpmnEvent) {
        if (!bpmnEvent.extensionElements)
          bpmnEvent.extensionElements = moddle.create('bpmn:ExtensionElements');
        const extensions = bpmnEvent.extensionElements.get('values');
        const extension = extensions.find(ext => ext.$instanceOf(extensionName));
        if (!extension) {
          const newExt = moddle.create(extensionName);
          newExt.value = value;
          extensions.push(newExt);
        } else
          extension.value = value;
      } // not sure what to do if the event hasn't been set
    };

    if (catching) {
      return TextFieldEntry({
        element,
        id: `${idPrefix}-variable-name`,
        description: description,
        label: translate(label),
        getValue,
        setValue,
        debounce,
      });
    } else {
      return TextAreaEntry({
        element,
        id: `${idPrefix}-payload-expression`,
        description: description,
        label: translate(label),
        getValue,
        setValue,
        debounce,
      });
    }
  }
}

function getCodeTextField(eventDetails, label) {

  const { eventType, eventDefType, referenceType, idPrefix } = eventDetails;

  return function (props) {

    const { element, moddle, commandStack } = props;
    const translate = useService('translate');
    const debounce = useService('debounceInput');
    const attrName = `${idPrefix}Code`;

    const getEvent = () => {
      const eventDef = element.businessObject.eventDefinitions.find(v => v.$type == eventDefType);
      const bpmnEvent = eventDef.get(referenceType);
      return bpmnEvent;
    };

    const getValue = () => {
      const bpmnEvent = getEvent();
      return (bpmnEvent) ? bpmnEvent.get(attrName) : null;
    };

    const setValue = (value) => {
      const bpmnEvent = getEvent();
      if (bpmnEvent)
        bpmnEvent.set(attrName, value);
    };

    return TextFieldEntry({
      element,
      id: `${idPrefix}-code-value`,
      label: translate(label),
      getValue,
      setValue,
      debounce,
    });
  }
}

export { hasEventType, getSelectorForType, getConfigureGroupForType, replaceGroup };
