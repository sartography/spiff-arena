import {
  Button,
  Form,
  Modal,
  Stack,
  TextInput,
  ContainedList,
  ContainedListItem,
  Grid,
  Column,
} from '@carbon/react';
import { Close, Add } from '@carbon/icons-react';
import React, { useState } from 'react';
import {
  CorrelationKey,
  CorrelationProperty,
  Message,
  ProcessGroup,
  RetrievalExpression,
} from '../../interfaces';
import { findMessagesForCorrelationKey } from './MessageHelper';

type OwnProps = {
  correlationKey: CorrelationKey;
  processGroup: ProcessGroup;
  open: boolean;
  onClose: () => void;
  onSave: (updatedProcessGroup: ProcessGroup) => void;
};

export default function CorrelationModal({
  correlationKey,
  processGroup,
  open,
  onClose,
  onSave,
}: OwnProps) {
  const getProperties = () => {
    const properties: string[] = [];
    if (correlationKey) {
      correlationKey.correlation_properties.forEach((prop: string) => {
        properties.push(prop);
      });
    }
    return properties;
  };

  const [invalidCorrelationName, setInvalidCorrelationName] =
    useState<boolean>(false);
  const [invalidPropertyName, setInvalidPropertyName] =
    useState<boolean>(false);
  const [newProperty, setNewProperty] = useState<string>('');
  const [properties, setProperties] = useState<string[]>(getProperties);
  const [newName, setNewName] = useState<string>(correlationKey.id);

  let existingNames: string[] = [];
  if (processGroup.correlation_keys) {
    existingNames = processGroup.correlation_keys
      .filter((key: CorrelationKey) => {
        return key.id !== correlationKey.id;
      })
      .map((msg: Message) => {
        return msg.id;
      });
  }

  const validCorrelationName = (name: string): boolean => {
    return (
      name.length >= 3 &&
      /^[a-z0-9_]+$/.test(name) &&
      !existingNames.includes(name)
    );
  };

  const validPropertyName = (name: string): boolean => {
    return (
      name.length >= 3 &&
      /^[a-z0-9_]+$/.test(name) &&
      !properties.includes(name)
    );
  };

  const propertiesList = () => {
    const listItems = properties.map((prop: string) => {
      const itemAction = (
        <Button
          kind="ghost"
          iconDescription="Remove"
          hasIconOnly
          renderIcon={Close}
          onClick={() => {
            setProperties(properties.filter((p) => p !== prop));
          }}
        />
      );
      return <ContainedListItem action={itemAction}>{prop}</ContainedListItem>;
    });
    return (
      <ContainedList label="Correlation Properties" kind="on-page" action="">
        {listItems}
      </ContainedList>
    );
  };

  const createCorrelationForm = () => {
    return (
      <Form onSubmit={onClose}>
        <Stack gap={5}>
          <TextInput
            id="correlation_name"
            name="correlation_name"
            placeholder="table"
            invalidText='Must be unique, have a minimum of 3 letters, please use only letters and underscores, ie "table"'
            invalid={invalidCorrelationName}
            labelText="Correlation Name*"
            defaultValue={newName}
            onChange={(event: any) => {
              setNewName(event.target.value);
              console.log(
                'Setting invalid correlation name to ',
                !validCorrelationName(event.target.value)
              );
              setInvalidCorrelationName(
                !validCorrelationName(event.target.value)
              );
            }}
          />
          {propertiesList()}
          <Grid>
            <Column lg={4}>
              <TextInput
                id="new_property"
                name="new_property"
                placeholder="table_number"
                invalidText='Must be unique, have a minimum of 3 letters, please use only letters and underscores, ie "table_number"'
                invalid={invalidPropertyName}
                onChange={(event: any) => {
                  setNewProperty(event.target.value);
                  setInvalidPropertyName(
                    !validPropertyName(event.target.value)
                  );
                }}
              />
            </Column>
            <Column lg={4}>
              <Button
                data-qa="add-property-button"
                renderIcon={Add}
                iconDescription="Add Property"
                hasIconOnly
                size="sm"
                kind=""
                onClick={() => {
                  if (validPropertyName(newProperty)) {
                    console.log('Adding Property ', newProperty);
                    setProperties(properties.concat(newProperty));
                  }
                }}
              />
            </Column>
          </Grid>
        </Stack>
      </Form>
    );
  };

  const saveModel = () => {
    if (!validCorrelationName(newName)) {
      console.log('Invalid correlation name');
      return;
    }
    const updatedProcessGroup = JSON.parse(JSON.stringify(processGroup));
    let updatedCorrelationKey = updatedProcessGroup.correlation_keys.find(
      (key: CorrelationKey) => {
        return key.id === correlationKey.id;
      }
    );
    if (!updatedCorrelationKey) {
      updatedCorrelationKey = { id: newName, correlation_properties: [] };
      updatedProcessGroup.correlation_keys.push(updatedCorrelationKey);
    }
    // Update the correlation key
    updatedCorrelationKey.id = newName;
    updatedCorrelationKey.correlation_properties = properties;

    const connectedMessages = findMessagesForCorrelationKey(
      processGroup,
      correlationKey
    );
    const connectedMessageIds = connectedMessages.map((msg: Message) => {
      return msg.id;
    });

    // Remove retrieval expressions for connected messages if those properties no longer exist in the correlation key
    updatedProcessGroup.correlation_properties.forEach(
      (prop: CorrelationProperty) => {
        console.log(prop, properties);
        if (!(prop.id in properties)) {
          // eslint-disable-next-line no-param-reassign
          prop.retrieval_expressions = prop.retrieval_expressions.filter(
            (re: RetrievalExpression) => {
              return !connectedMessageIds.includes(re.message_ref);
            }
          );
        }
      }
    );
    updatedProcessGroup.correlation_properties =
      updatedProcessGroup.correlation_properties.filter(
        (prop: CorrelationProperty) => {
          return prop.retrieval_expressions.length > 0;
        }
      );

    // assure retrieval expressions exist for all connected messages for all properties in the correlation key
    properties.forEach((prop: string) => {
      let cp = updatedProcessGroup.correlation_properties.find(
        (ecp: CorrelationProperty) => {
          return ecp.id === prop;
        }
      );
      if (!cp) {
        cp = { id: prop, retrieval_expressions: [] };
        updatedProcessGroup.correlation_properties.push(cp);
      }
      connectedMessages.forEach((msg: Message) => {
        let re = cp.retrieval_expressions.find((ere: RetrievalExpression) => {
          return ere.message_ref === msg.id;
        });
        if (!re) {
          re = { message_ref: msg.id, formal_expression: cp.id };
          cp.retrieval_expressions.push(re);
        }
      });
    });
    onSave(updatedProcessGroup);
    onClose();
  };

  return (
    <Modal
      open={open}
      onRequestClose={onClose}
      modalHeading={`${correlationKey.id}`}
      modalLabel="Details"
      primaryButtonText="Save"
      secondaryButtonText="Cancel"
      onSecondarySubmit={onClose}
      primaryButtonDisabled={invalidCorrelationName}
      onRequestSubmit={saveModel}
    >
      {createCorrelationForm()}
    </Modal>
  );
}
