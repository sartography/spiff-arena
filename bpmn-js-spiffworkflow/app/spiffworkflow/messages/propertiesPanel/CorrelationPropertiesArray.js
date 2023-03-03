import { useService } from 'bpmn-js-properties-panel';
import {
  SelectEntry,
  isTextFieldEntryEdited,
  TextFieldEntry,
} from '@bpmn-io/properties-panel';
import {
  getRoot,
  findCorrelationKeys,
  findCorrelationProperties,
  findCorrelationKeyForCorrelationProperty,
} from '../MessageHelpers';
import { removeFirstInstanceOfItemFromArrayInPlace } from '../../helpers';

/**
 * Allows the creation, or editing of messageCorrelations at the bpmn:sendTask level of a BPMN document.
 */
export function CorrelationPropertiesArray(props) {
  const { moddle } = props;
  const { element } = props;
  const { commandStack } = props;
  const { translate } = props;

  const correlationPropertyArray = findCorrelationProperties(
    element.businessObject
  );
  const items = correlationPropertyArray.map(
    (correlationPropertyModdleElement, index) => {
      const id = `correlation-${index}`;
      const entries = MessageCorrelationPropertyGroup({
        idPrefix: id,
        correlationPropertyModdleElement,
        translate,
        element,
        commandStack,
        moddle,
      });
      return {
        id,
        label: correlationPropertyModdleElement.name,
        entries,
        autoFocusEntry: id,
        remove: removeFactory({
          element,
          correlationPropertyModdleElement,
          commandStack,
          moddle,
        }),
      };
    }
  );

  function add(event) {
    event.stopPropagation();
    const newCorrelationPropertyElement = moddle.create(
      'bpmn:CorrelationProperty'
    );
    const correlationPropertyId = moddle.ids.nextPrefixed(
      'CorrelationProperty_'
    );
    newCorrelationPropertyElement.id = correlationPropertyId;
    newCorrelationPropertyElement.name = correlationPropertyId;
    const rootElement = getRoot(element.businessObject);
    const { rootElements } = rootElement;
    rootElements.push(newCorrelationPropertyElement);

    const correlationKeyElements = findCorrelationKeys(
      newCorrelationPropertyElement,
      moddle
    );
    const correlationKeyElement = correlationKeyElements[0];
    if (correlationKeyElement.correlationPropertyRef) {
      correlationKeyElement.correlationPropertyRef.push(
        newCorrelationPropertyElement
      );
    } else {
      correlationKeyElement.correlationPropertyRef = [
        newCorrelationPropertyElement,
      ];
    }

    commandStack.execute('element.updateProperties', {
      element,
      properties: {},
    });
  }

  return { items, add };
}

function removeFactory(props) {
  const { element, correlationPropertyModdleElement, moddle, commandStack } =
    props;

  return function (event) {
    event.stopPropagation();
    const rootElement = getRoot(element.businessObject);
    const { rootElements } = rootElement;

    const oldCorrelationKeyElement = findCorrelationKeyForCorrelationProperty(
      correlationPropertyModdleElement,
      moddle
    );
    if (oldCorrelationKeyElement) {
      removeFirstInstanceOfItemFromArrayInPlace(
        oldCorrelationKeyElement.correlationPropertyRef,
        correlationPropertyModdleElement
      );
    }

    removeFirstInstanceOfItemFromArrayInPlace(
      rootElements,
      correlationPropertyModdleElement
    );
    commandStack.execute('element.updateProperties', {
      element,
      properties: {
        messages: rootElements,
      },
    });
  };
}

function MessageCorrelationPropertyGroup(props) {
  const {
    idPrefix,
    correlationPropertyModdleElement,
    translate,
    element,
    commandStack,
    moddle,
  } = props;
  return [
    {
      id: `${idPrefix}-correlation-key`,
      component: MessageCorrelationKeySelect,
      isEdited: isTextFieldEntryEdited,
      idPrefix,
      element,
      correlationPropertyModdleElement,
      translate,
      moddle,
      commandStack,
    },
    {
      id: `${idPrefix}-correlation-property-name`,
      component: CorrelationPropertyNameTextField,
      isEdited: isTextFieldEntryEdited,
      idPrefix,
      element,
      correlationPropertyModdleElement,
      translate,
      commandStack,
    },
  ];
}

function MessageCorrelationKeySelect(props) {
  const {
    idPrefix,
    correlationPropertyModdleElement,
    translate,
    element,
    moddle,
    commandStack,
  } = props;
  const debounce = useService('debounceInput');

  const setValue = (value) => {
    if (
      value === 'placeholder-never-should-be-used-as-an-actual-correlation-key'
    ) {
      return;
    }
    const correlationKeyElements = findCorrelationKeys(
      correlationPropertyModdleElement,
      moddle
    );
    let newCorrelationKeyElement;
    for (const cke of correlationKeyElements) {
      if (cke.name === value) {
        newCorrelationKeyElement = cke;
      }
    }
    const oldCorrelationKeyElement = findCorrelationKeyForCorrelationProperty(
      correlationPropertyModdleElement,
      moddle
    );

    if (newCorrelationKeyElement.correlationPropertyRef) {
      newCorrelationKeyElement.correlationPropertyRef.push(
        correlationPropertyModdleElement
      );
    } else {
      newCorrelationKeyElement.correlationPropertyRef = [
        correlationPropertyModdleElement,
      ];
    }

    if (oldCorrelationKeyElement) {
      removeFirstInstanceOfItemFromArrayInPlace(
        oldCorrelationKeyElement.correlationPropertyRef,
        correlationPropertyModdleElement
      );
    }

    commandStack.execute('element.updateModdleProperties', {
      element,
      moddleElement: correlationPropertyModdleElement,
      properties: {},
    });
  };

  const getValue = () => {
    const correlationKeyElement = findCorrelationKeyForCorrelationProperty(
      correlationPropertyModdleElement,
      moddle
    );
    if (correlationKeyElement) {
      return correlationKeyElement.name;
    }
    return null;
  };

  const getOptions = () => {
    const correlationKeyElements = findCorrelationKeys(
      correlationPropertyModdleElement,
      moddle
    );
    const options = [];
    if (correlationKeyElements.length === 0) {
      options.push({
        label: 'Please Create a Correlation Key',
        value: 'placeholder-never-should-be-used-as-an-actual-correlation-key',
        disabled: true,
      });
    }
    for (const correlationKeyElement of correlationKeyElements) {
      options.push({
        label: correlationKeyElement.name,
        value: correlationKeyElement.name,
      });
    }
    return options;
  };

  return SelectEntry({
    id: `${idPrefix}-select`,
    element,
    label: translate('Correlation Key'),
    getValue,
    setValue,
    getOptions,
    debounce,
  });
}

function CorrelationPropertyIdTextField(props) {
  const {
    id,
    element,
    correlationPropertyModdleElement,
    commandStack,
    translate,
  } = props;

  const debounce = useService('debounceInput');
  const setValue = (value) => {
    commandStack.execute('element.updateModdleProperties', {
      element,
      moddleElement: correlationPropertyModdleElement,
      properties: {
        id: value,
      },
    });
  };

  const getValue = () => {
    return correlationPropertyModdleElement.id;
  };

  return TextFieldEntry({
    element,
    id: `${id}-id-textField`,
    label: translate('ID'),
    getValue,
    setValue,
    debounce,
  });
}

function CorrelationPropertyNameTextField(props) {
  const {
    id,
    element,
    correlationPropertyModdleElement,
    commandStack,
    translate,
  } = props;

  const debounce = useService('debounceInput');
  const setValue = (value) => {
    commandStack.execute('element.updateModdleProperties', {
      element,
      moddleElement: correlationPropertyModdleElement,
      properties: {
        name: value,
      },
    });
  };

  const getValue = () => {
    return correlationPropertyModdleElement.name;
  };

  return TextFieldEntry({
    element,
    id: `${id}-name-textField`,
    label: translate('Name'),
    getValue,
    setValue,
    debounce,
  });
}
