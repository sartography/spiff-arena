import { HeaderButton } from '@bpmn-io/properties-panel';
import { useService } from 'bpmn-js-properties-panel';
import {getExtensionValue, setExtensionValue} from '../extensionHelpers';

/**
 * Sends a notification to the host application saying the user
 * would like to edit something.  Hosting application can then
 * update the value and send it back.
 */
export function SpiffExtensionLaunchButton(props) {
  const { element, name, event, listenEvent } = props;
  const eventBus = useService('eventBus');
  return HeaderButton({
    className: 'spiffworkflow-properties-panel-button',
    id: `launch_editor_button_${name}`,
    onClick: () => {
      const value = getExtensionValue(element, name);
      eventBus.fire(event, {
        value,
        eventBus,
        listenEvent,
      });

      // Listen for a response if the listenEvent is provided, and
      // set the value to the response
      // Optional additional arguments if we should listen for a reponse.
      if (listenEvent) {
        const { commandStack, moddle } = props;
        // Listen for a response, to update the script.
        eventBus.once(listenEvent, (response) => {
          setExtensionValue(element, name, response.value, moddle, commandStack);
        });
      }

    },
    children: 'Launch Editor',
  });
}
