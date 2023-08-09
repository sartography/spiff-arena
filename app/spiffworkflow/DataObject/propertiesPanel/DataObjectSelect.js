import {useService } from 'bpmn-js-properties-panel';
import { SelectEntry } from '@bpmn-io/properties-panel';
import {findDataObjects, idToHumanReadableName} from '../DataObjectHelpers';

/**
 * Finds the value of the given type within the extensionElements
 * given a type of "spiff:preScript", would find it in this, and return
 * the object.
 *
 *  <bpmn:
 <bpmn:userTask id="123" name="My User Task!">
 <bpmn:extensionElements>
 <spiffworkflow:preScript>
 me = "100% awesome"
 </spiffworkflow:preScript>
 </bpmn:extensionElements>
 ...
 </bpmn:userTask>
 *
 * @returns {string|null|*}
 */
export function DataObjectSelect(props) {
  const element = props.element;
  const commandStack = props.commandStack;
  const debounce = useService('debounceInput');


  const getValue = () => {
    return element.businessObject.dataObjectRef.id
  }

  const setValue = value => {
    const businessObject = element.businessObject;
    const dataObjects = findDataObjects(businessObject.$parent)
    for (const flowElem of dataObjects) {
      if (flowElem.$type === 'bpmn:DataObject' && flowElem.id === value) {
        commandStack.execute('element.updateModdleProperties', {
          element,
          moddleElement: businessObject,
          properties: {
            dataObjectRef: flowElem
          }
        });
        commandStack.execute('element.updateProperties', {
          element,
          moddleElement: businessObject,
          properties: {
            'name': idToHumanReadableName(flowElem.id)
          }
        });
      }
    }
  }

  const getOptions = value => {
    const businessObject = element.businessObject;
    const parent = businessObject.$parent;
    let dataObjects = findDataObjects(parent);
    let options = [];
    dataObjects.forEach(dataObj => {
      options.push({label: dataObj.id, value: dataObj.id})
    });
    return options;
  }

  return <SelectEntry
    id={'selectDataObject'}
    element={element}
    description={"Select the Data Object this represents."}
    label={"Which Data Object does this reference?"}
    getValue={ getValue }
    setValue={ setValue }
    getOptions={ getOptions }
    debounce={debounce}
  />;

}
