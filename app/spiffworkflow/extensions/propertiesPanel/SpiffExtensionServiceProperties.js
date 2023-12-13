import { useService } from 'bpmn-js-properties-panel';
import { TextFieldEntry, SelectEntry } from '@bpmn-io/properties-panel';
import { SPIFFWORKFLOW_XML_NAMESPACE } from '../../constants';

let serviceTaskOperators = [];

// This stores the parameters for a given service task operator
//  so that we can remember the values when switching between them
// the values should be the list of moddle elements that we push onto
//  the parameterList of service task operator and the key should be
//  the service task operator id
const previouslyUsedServiceTaskParameterValuesHash = {};

const LOW_PRIORITY = 500;
// I'm not going to change these variable names, but this is actually the name of the modeller
// type (as defined in moddle/spiffworkflow.json) NOT the element name (which is lowercase)
const SERVICE_TASK_OPERATOR_ELEMENT_NAME = `${SPIFFWORKFLOW_XML_NAMESPACE}:ServiceTaskOperator`;
const SERVICE_TASK_PARAMETERS_ELEMENT_NAME = `${SPIFFWORKFLOW_XML_NAMESPACE}:Parameters`;
const SERVICE_TASK_PARAMETER_ELEMENT_NAME = `${SPIFFWORKFLOW_XML_NAMESPACE}:Parameter`;

/**
 * A generic properties' editor for text input.
 * Allows you to provide additional SpiffWorkflow extension properties.  Just
 * uses whatever name is provide on the property, and adds or updates it as
 * needed.
 *
 *
    <bpmn:serviceTask id="service_task_one" name="Service Task One">
      <bpmn:extensionElements>
        <spiffworkflow:serviceTaskOperator id="SlackWebhookOperator" resultVariable="result">
          <spiffworkflow:parameters>
            <spiffworkflow:parameter name="webhook_token" type="string" value="token" />
            <spiffworkflow:parameter name="message" type="string" value="ServiceTask testing" />
            <spiffworkflow:parameter name="channel" type="string" value="#" />
          </spiffworkflow:parameters>
        </spiffworkflow:serviceTaskOperator>
      </bpmn:extensionElements>
    </bpmn:serviceTask>
 *
 * @returns {string|null|*}
 */

function requestServiceTaskOperators(eventBus, element, commandStack) {
  eventBus.fire('spiff.service_tasks.requested', { eventBus });
  eventBus.on('spiff.service_tasks.returned', (event) => {
    if (event.serviceTaskOperators.length > 0) {
      serviceTaskOperators = event.serviceTaskOperators;
    }
  });
}

function getServiceTaskOperatorModdleElement(shapeElement) {
  const { extensionElements } = shapeElement.businessObject;
  if (extensionElements) {
    for (const ee of extensionElements.values) {
      if (ee.$type === SERVICE_TASK_OPERATOR_ELEMENT_NAME) {
        return ee;
      }
    }
  }
  return null;
}

function getServiceTaskParameterModdleElements(shapeElement) {
  const serviceTaskOperatorModdleElement =
    getServiceTaskOperatorModdleElement(shapeElement);
  if (serviceTaskOperatorModdleElement) {
    const { parameterList } = serviceTaskOperatorModdleElement;
    if (parameterList) {
      return parameterList.parameters;
    }
  }
  return [];
}

export function ServiceTaskOperatorSelect(props) {
  const { element } = props;
  const { commandStack } = props;
  const { translate } = props;
  const { moddle } = props;

  const debounce = useService('debounceInput');
  const eventBus = useService('eventBus');

  if (serviceTaskOperators.length === 0) {
    requestServiceTaskOperators(eventBus, element, commandStack);
  }

  const getValue = () => {
    const serviceTaskOperatorModdleElement =
      getServiceTaskOperatorModdleElement(element);
    if (serviceTaskOperatorModdleElement) {
      return serviceTaskOperatorModdleElement.id;
    }
    return '';
  };

  const setValue = (value) => {
    if (!value) {
      return;
    }

    const serviceTaskOperator = serviceTaskOperators.find(
      (sto) => sto.id === value
    );
    if (!serviceTaskOperator) {
      console.error(`Could not find service task operator with id: ${value}`);
      return;
    }
    if (!(element.businessObject.id in previouslyUsedServiceTaskParameterValuesHash)) {
      previouslyUsedServiceTaskParameterValuesHash[element.businessObject.id] = {}
    }
    const previouslyUsedServiceTaskParameterValues =
      previouslyUsedServiceTaskParameterValuesHash[element.businessObject.id][value];

    const { businessObject } = element;
    let extensions = businessObject.extensionElements;
    if (!extensions) {
      extensions = moddle.create('bpmn:ExtensionElements');
    }

    const oldServiceTaskOperatorModdleElement =
      getServiceTaskOperatorModdleElement(element);

    const newServiceTaskOperatorModdleElement = moddle.create(
      SERVICE_TASK_OPERATOR_ELEMENT_NAME
    );
    newServiceTaskOperatorModdleElement.id = value;
    let newParameterList;

    if (previouslyUsedServiceTaskParameterValues) {
      newParameterList = previouslyUsedServiceTaskParameterValues;
    } else {
      newParameterList = moddle.create(SERVICE_TASK_PARAMETERS_ELEMENT_NAME);
      newParameterList.parameters = [];
      serviceTaskOperator.parameters.forEach((stoParameter) => {
        const newParameterModdleElement = moddle.create(
          SERVICE_TASK_PARAMETER_ELEMENT_NAME
        );
        newParameterModdleElement.id = stoParameter.id;
        newParameterModdleElement.type = stoParameter.type;
        newParameterList.parameters.push(newParameterModdleElement);
      });

      previouslyUsedServiceTaskParameterValuesHash[element.businessObject.id][
        value
      ] = newParameterList;
      if (oldServiceTaskOperatorModdleElement) {
        previouslyUsedServiceTaskParameterValuesHash[element.businessObject.id][
          oldServiceTaskOperatorModdleElement.id
        ] = oldServiceTaskOperatorModdleElement.parameterList;
      }
    }

    newServiceTaskOperatorModdleElement.parameterList = newParameterList;

    const newExtensionValues = extensions.get('values').filter((extValue) => {
      return extValue.$type !== SERVICE_TASK_OPERATOR_ELEMENT_NAME;
    });
    newExtensionValues.push(newServiceTaskOperatorModdleElement);
    extensions.values = newExtensionValues;
    businessObject.extensionElements = extensions;

    commandStack.execute('element.updateModdleProperties', {
      element,
      moddleElement: businessObject,
      properties: {},
    });
  };

  const getOptions = () => {
    const optionList = [];
    if (serviceTaskOperators) {
      serviceTaskOperators.forEach((sto) => {
        optionList.push({
          label: sto.id,
          value: sto.id,
        });
      });
    }
    return optionList;
  };

  return SelectEntry({
    id: 'selectOperatorId',
    element,
    label: translate('Operator ID'),
    getValue,
    setValue,
    getOptions,
    debounce,
  });
}

export function ServiceTaskParameterArray(props) {
  const { element, commandStack } = props;

  const serviceTaskParameterModdleElements =
    getServiceTaskParameterModdleElements(element);
  const items = serviceTaskParameterModdleElements.map(
    (serviceTaskParameterModdleElement, index) => {
      const id = `serviceTaskParameter-${index}`;
      return {
        id,
        label: serviceTaskParameterModdleElement.id,
        entries: serviceTaskParameterEntries({
          idPrefix: id,
          element,
          serviceTaskParameterModdleElement,
          commandStack,
        }),
        autoFocusEntry: id,
      };
    }
  );
  return { items };
}

function serviceTaskParameterEntries(props) {
  const { idPrefix, serviceTaskParameterModdleElement, commandStack } = props;
  return [
    {
      idPrefix: `${idPrefix}-parameter`,
      component: ServiceTaskParameterTextField,
      serviceTaskParameterModdleElement,
      commandStack,
    },
  ];
}

function ServiceTaskParameterTextField(props) {
  const { idPrefix, element, serviceTaskParameterModdleElement, commandStack } = props;

  const debounce = useService('debounceInput');

  const setValue = (value) => {
    commandStack.execute('element.updateModdleProperties', {
      element,
      moddleElement: serviceTaskParameterModdleElement,
      properties: {
        value: value,
      },
    });
  };


  const getValue = () => {
    return serviceTaskParameterModdleElement.value;
  };

  return TextFieldEntry({
    element,
    id: `${idPrefix}-textField`,
    getValue,
    setValue,
    debounce,
  });
}

export function ServiceTaskResultTextInput(props) {
  const { element, translate, commandStack } = props;

  const debounce = useService('debounceInput');
  const serviceTaskOperatorModdleElement =
    getServiceTaskOperatorModdleElement(element);

  const setValue = (value) => {
    commandStack.execute('element.updateModdleProperties', {
      element,
      moddleElement: serviceTaskOperatorModdleElement,
      properties: {
        resultVariable: value,
      },
    });
  };

  const getValue = () => {
    if (serviceTaskOperatorModdleElement) {
      return serviceTaskOperatorModdleElement.resultVariable;
    }
    return '';
  };

  if (serviceTaskOperatorModdleElement) {
    return TextFieldEntry({
      element,
      label: translate('Response Variable'),
      description: translate(
        'response will be saved to this variable.  Leave empty to discard the response.'
      ),
      id: `result-textField`,
      getValue,
      setValue,
      debounce,
    });
  }
  return null;
}
