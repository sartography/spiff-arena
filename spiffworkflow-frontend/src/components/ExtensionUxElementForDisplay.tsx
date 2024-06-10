import { ReactElement } from 'react';
import { UiSchemaUxElement } from '../extension_ui_schema_interfaces';

type OwnProps = {
  displayLocation: string;
  elementCallback: Function;
  extensionUxElements?: UiSchemaUxElement[] | null;
};

export function ExtensionUxElementMap({
  displayLocation,
  elementCallback,
  extensionUxElements,
}: OwnProps) {
  if (!extensionUxElements) {
    return null;
  }

  const mainElement = () => {
    const elementsForDisplayLocation = extensionUxElements.filter(
      (uxElement: UiSchemaUxElement) => {
        return uxElement.display_location === displayLocation;
      },
    );
    return elementsForDisplayLocation.map(
      (uxElement: UiSchemaUxElement, index: number) => {
        return elementCallback(uxElement, index);
      },
    );
  };
  return mainElement();
}

export default function ExtensionUxElementForDisplay(
  args: OwnProps,
): ReactElement | null {
  const result = ExtensionUxElementMap(args);
  if (result === null) {
    return null;
  }
  // eslint-disable-next-line react/jsx-no-useless-fragment
  return <>{result}</>;
}
