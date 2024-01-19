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
    let foundElement = false;
    const elementMap = extensionUxElements.map(
      (uxElement: UiSchemaUxElement, index: number) => {
        if (uxElement.display_location === displayLocation) {
          foundElement = true;
          return elementCallback(uxElement, index);
        }
        return null;
      }
    );
    if (!foundElement && elementCallbackIfNotFound) {
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
