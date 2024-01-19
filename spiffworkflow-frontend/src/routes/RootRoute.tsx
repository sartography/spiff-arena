import { Loading } from '@carbon/react';
import ExtensionUxElementForDisplay from '../components/ExtensionUxElementForDisplay';
import TaskRouteTabs from '../components/TaskRouteTabs';
import { UiSchemaUxElement } from '../extension_ui_schema_interfaces';
import Extension from './Extension';
import InProgressInstances from './InProgressInstances';
import OnboardingView from './OnboardingView';

type OwnProps = {
  extensionUxElements?: UiSchemaUxElement[] | null;
};

export default function RootRoute({ extensionUxElements }: OwnProps) {
  const elementCallback = () => {
    return <Extension pageIdentifier="/my-time-tracking-report" />;
  };

  const defaultPageElements = () => {
    return (
      <>
        <OnboardingView />
        <TaskRouteTabs />
        <InProgressInstances />
      </>
    );
  };

  if (extensionUxElements) {
    return (
      <ExtensionUxElementForDisplay
        displayLocation="home_page"
        elementCallback={elementCallback}
        extensionUxElements={extensionUxElements}
        elementCallbackIfNotFound={defaultPageElements}
      />
    );
  }

  const style = { margin: '50px 0 50px 50px' };
  return (
    <Loading
      description="Active loading indicator"
      withOverlay={false}
      style={style}
    />
  );
}
