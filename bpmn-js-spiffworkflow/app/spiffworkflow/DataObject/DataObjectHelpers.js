/**
 * Returns the moddelElement if it is a process, otherwise, returns the
 *
 * @param container
 */

export function findDataObjects(parent, dataObjects) {
  if (typeof(dataObjects) === 'undefined')
    dataObjects = [];
  let process;
  if (!parent) {
    return [];
  }
  if (parent.processRef) {
    process = parent.processRef;
  } else {
    process = parent;
    if (process.$type === 'bpmn:SubProcess')
      findDataObjects(process.$parent, dataObjects);
  }
  if (typeof(process.flowElements) !== 'undefined') {
    for (const element of process.flowElements) {
      if (element.$type === 'bpmn:DataObject')
        dataObjects.push(element);
    }
  }
  return dataObjects;
}

export function findDataObject(process, id) {
  for (const dataObj of findDataObjects(process)) {
    if (dataObj.id === id) {
      return dataObj;
    }
  }
}

export function findDataObjectReferences(children, dataObjectId) {
  if (children == null) {
    return [];
  }
  return children.flatMap((child) => {
    if (child.$type == 'bpmn:DataObjectReference' && child.dataObjectRef.id == dataObjectId)
      return [child];
    else if (child.$type == 'bpmn:SubProcess')
      return findDataObjectReferences(child.get('flowElements'), dataObjectId);
    else
      return [];
  });
}

export function findDataObjectReferenceShapes(children, dataObjectId) {
  return children.flatMap((child) => {
    if (child.type == 'bpmn:DataObjectReference' && child.businessObject.dataObjectRef.id == dataObjectId)
      return [child];
    else if (child.type == 'bpmn:SubProcess')
      return findDataObjectReferenceShapes(child.children, dataObjectId);
    else
      return [];
  });
}

export function idToHumanReadableName(id) {
  const words = id.match(/[A-Za-z][a-z]*|[0-9]+/g) || [id];
  return words.map(capitalize).join(' ');

  function capitalize(word) {
    return word.charAt(0).toUpperCase() + word.substring(1);
  }
}
