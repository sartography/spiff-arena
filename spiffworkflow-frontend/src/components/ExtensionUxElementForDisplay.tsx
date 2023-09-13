import { UiSchemaUxElement } from '../extension_ui_schema_interfaces';

type OwnProps = {
  displayLocation: string;
  elementCallback: Function;
  extensionUxElements?: UiSchemaUxElement[] | null;
};

export default function ExtensionUxElementForDisplay({
  displayLocation,
  elementCallback,
  extensionUxElements,
}: OwnProps) {
  if (!extensionUxElements) {
    return null;
  }

  const mainElement = () => {
    return extensionUxElements.map(
      (uxElement: UiSchemaUxElement, index: number) => {
        if (uxElement.display_location === displayLocation) {
          return elementCallback(uxElement, index);
        }
        return null;
      }
    );
  };

  return <>{mainElement()}</>;
}
