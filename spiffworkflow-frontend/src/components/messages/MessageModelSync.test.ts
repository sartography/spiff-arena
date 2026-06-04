import { describe, expect, it } from 'vitest';
import {
  hasUnsyncedBpmnMessage,
  syncBpmnMessagesToMessageModels,
} from './MessageModelSync';

const bpmnXml = `
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
  <bpmn:message id="Message_SystemMessageNotification" name="SystemErrorMessage" />
  <bpmn:correlationProperty id="message_text" name="message_text">
    <bpmn:correlationPropertyRetrievalExpression messageRef="Message_SystemMessageNotification">
      <bpmn:formalExpression>message_text</bpmn:formalExpression>
    </bpmn:correlationPropertyRetrievalExpression>
  </bpmn:correlationProperty>
  <bpmn:correlationProperty id="recipients" name="recipients">
    <bpmn:correlationPropertyRetrievalExpression messageRef="Message_SystemMessageNotification">
      <bpmn:messagePath>recipients</bpmn:messagePath>
    </bpmn:correlationPropertyRetrievalExpression>
  </bpmn:correlationProperty>
</bpmn:definitions>
`;

describe('MessageModelSync', () => {
  it('does not report an unsynced message when correlation properties match', () => {
    expect(
      hasUnsyncedBpmnMessage(bpmnXml, 'misc/system-message-notification', [
        {
          identifier: 'Message_SystemMessageNotification',
          location: 'misc',
          correlation_properties: [
            {
              identifier: 'message_text',
              retrieval_expression: 'message_text',
            },
            {
              identifier: 'recipients',
              retrieval_expression: 'recipients',
            },
          ],
        },
      ]),
    ).toBe(false);
  });

  it('reports an unsynced message when saved correlation properties differ', () => {
    expect(
      hasUnsyncedBpmnMessage(bpmnXml, 'misc/system-message-notification', [
        {
          identifier: 'Message_SystemMessageNotification',
          location: 'misc',
          correlation_properties: [
            {
              identifier: 'message_text',
              retrieval_expression: 'changed_message_text',
            },
          ],
        },
      ]),
    ).toBe(true);
  });

  it('accepts a saved model keyed by BPMN message name instead of id', () => {
    expect(
      hasUnsyncedBpmnMessage(bpmnXml, 'misc/system-message-notification', [
        {
          identifier: 'SystemErrorMessage',
          location: 'misc',
          correlation_properties: [
            {
              identifier: 'message_text',
              retrieval_expression: 'message_text',
            },
            {
              identifier: 'recipients',
              retrieval_expression: 'recipients',
            },
          ],
        },
      ]),
    ).toBe(false);
  });

  it('syncs BPMN message correlation properties from the saved message model', () => {
    const messageModels = [
      {
        identifier: 'Message_SystemMessageNotification',
        location: 'misc',
        correlation_properties: [
          {
            identifier: 'message_text',
            retrieval_expression: 'changed_message_text',
          },
        ],
      },
    ];

    const syncedXml = syncBpmnMessagesToMessageModels(
      bpmnXml,
      'misc/system-message-notification',
      messageModels,
    );

    expect(syncedXml).toContain('changed_message_text');
    expect(syncedXml).not.toContain('recipients');
    expect(
      hasUnsyncedBpmnMessage(
        syncedXml,
        'misc/system-message-notification',
        messageModels,
      ),
    ).toBe(false);
  });
});
