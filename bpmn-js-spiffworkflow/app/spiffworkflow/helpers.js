// https://stackoverflow.com/a/5767357/6090676
export function removeFirstInstanceOfItemFromArrayInPlace(arr, value) {
  const index = arr.indexOf(value);
  if (index > -1) {
    arr.splice(index, 1);
  }
  return arr;
}

export function removeExtensionElementsIfEmpty(moddleElement) {
  if (moddleElement.extensionElements.values.length < 1) {
    moddleElement.extensionElements = null;
  }
}

/**
 * loops up until it can find the root.
 * @param element
 */
export function getRoot(businessObject, moddle) {
  // HACK: get the root element. need a more formal way to do this
  if (moddle) {
    for (const elementId in moddle.ids._seed.hats) {
      if (elementId.startsWith('Definitions_')) {
        return moddle.ids._seed.hats[elementId];
      }
    }
  } else {
    // todo: Do we want businessObject to be a shape or moddle object?
    if (businessObject.$type === 'bpmn:Definitions') {
      return businessObject;
    }
    if (typeof businessObject.$parent !== 'undefined') {
      return getRoot(businessObject.$parent);
    }
  }
  return businessObject;
}
