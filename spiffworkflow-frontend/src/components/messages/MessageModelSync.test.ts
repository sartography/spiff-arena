import { describe, expect, it } from 'vitest';
import {
  getBpmnMessageSyncStatus,
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

const bpmnXmlWithDifferentMessageName = `
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
  <bpmn:correlationProperty id="mcp_topica_one" name="MCP TopicA One">
    <bpmn:correlationPropertyRetrievalExpression messageRef="message_send_one">
      <bpmn:formalExpression>topica_one</bpmn:formalExpression>
    </bpmn:correlationPropertyRetrievalExpression>
  </bpmn:correlationProperty>
  <bpmn:message id="message_send_one" name="Message Send One" />
</bpmn:definitions>
`;

const bpmnXmlWithSendTaskMessageRef = `
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
  <bpmn:process id="Process_kdchmsv" isExecutable="true">
    <bpmn:sendTask id="Activity_0v6kepv" name="Send jontesting" messageRef="jontesting" />
  </bpmn:process>
  <bpmn:message id="jontesting" name="jontesting" />
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

  it('reports a missing message model separately from changed correlation properties', () => {
    expect(
      getBpmnMessageSyncStatus(bpmnXml, 'misc/system-message-notification', []),
    ).toEqual({
      hasMissingMessageModel: true,
      missingMessageModelIdentifiers: ['SystemErrorMessage'],
      hasUnsyncedMessage: true,
    });
  });

  it('reports a missing message model referenced directly by a send task', () => {
    expect(
      getBpmnMessageSyncStatus(
        bpmnXmlWithSendTaskMessageRef,
        'misc/event-gateway-test',
        [],
      ),
    ).toEqual({
      hasMissingMessageModel: true,
      missingMessageModelIdentifiers: ['jontesting'],
      hasUnsyncedMessage: true,
    });
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

  it('syncs messages using the original BPMN messageRef when id and name differ', () => {
    const messageModels = [
      {
        identifier: 'Message Send One',
        location: 'misc/category_number_one',
        correlation_properties: [
          {
            identifier: 'mcp_topica_one',
            retrieval_expression: 'payload.topica_one',
          },
        ],
      },
    ];

    const syncedXml = syncBpmnMessagesToMessageModels(
      bpmnXmlWithDifferentMessageName,
      'misc/category_number_one/message-sender',
      messageModels,
    );

    expect(syncedXml).toContain('messageRef="message_send_one"');
    expect(syncedXml).not.toContain('messageRef="Message Send One"');
    expect(syncedXml).toContain('payload.topica_one');
    expect(
      hasUnsyncedBpmnMessage(
        syncedXml,
        'misc/category_number_one/message-sender',
        messageModels,
      ),
    ).toBe(false);
  });
});
