import { UiSchemaUxElement } from '../extension_ui_schema_interfaces';

type OwnProps = {
  displayLocation: string;
  elementCallback: Function;
  extensionUxElements?: UiSchemaUxElement[] | null;
  elementCallbackIfNotFound?: Function;
};

export function ExtensionUxElementMap({
  displayLocation,
  elementCallback,
  extensionUxElements,
  elementCallbackIfNotFound,
}: OwnProps) {
  if (!extensionUxElements) {
    return null;
  }

  const mainElement = () => {
    const elementsForDisplayLocation = extensionUxElements.filter(
      (uxElement: UiSchemaUxElement) => {
        return uxElement.display_location === displayLocation;
      }
    );
    const elementMap = elementsForDisplayLocation.map(
      (uxElement: UiSchemaUxElement, index: number) => {
        return elementCallback(uxElement, index);
      }
    );
    if (elementMap.length === 0 && elementCallbackIfNotFound) {
      return elementCallbackIfNotFound();
    }
    return elementMap;
  };
  return mainElement();
}

export default function ExtensionUxElementForDisplay(args: OwnProps) {
  const result = ExtensionUxElementMap(args);
  if (result === null) {
    return null;
  }
  return result;
}
