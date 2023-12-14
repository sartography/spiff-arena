import {
  Form,
  Modal,
  Stack,
  TextInput,
  Checkbox,
  Select,
  SelectItem,
} from '@carbon/react';
import { useEffect, useState } from 'react';
import { ReferenceCache } from '../../interfaces';
import HttpService from '../../services/HttpService';

type OwnProps = {
  messageModel: ReferenceCache;
  open: boolean;
  onClose: () => void;
};

export default function MessageModal({
  messageModel,
  open,
  onClose,
}: OwnProps) {
  const updatedModel: ReferenceCache = { ...messageModel };
  const [identifierInvalid, setIdentifierInvalid] = useState<boolean>(false);
  const [showCorrelations, setShowCorrelations] = useState<boolean>(false);
  const [correlationKeys, setCorrelationKeys] = useState<any>({ results: [] });
  const [correlationKey, setCorrelationKey] = useState<ReferenceCache | null>(
    null
  );

  setShowCorrelations(messageModel.properties.correlations.length > 0);

  useEffect(() => {
    let queryParamString = `per_page=100&page=1`;
    queryParamString += `&relative_location=${messageModel.relative_location}`;

    const updateKeys = (result: any) => {
      setCorrelationKeys(result);
      result.results.forEach((key: any) => {
        console.log("Has Key?", key.identifier, messageModel.properties.correlation_keys);
        if (messageModel.properties.correlation_keys.includes(key.identifier)) {
          console.log("Huston we have a match", key);
          setCorrelationKey(key);
          setShowCorrelations(true);
        }
      });
    };

    HttpService.makeCallToBackend({
      path: `/correlation-keys?${queryParamString}`,
      successCallback: updateKeys,
    });
  }, [messageModel]);

  const onMessageNameChange = (event: any) => {
    updatedModel.identifier = event.target.value;
    setIdentifierInvalid(
      updatedModel.identifier.length < 3 ||
        !/^[a-z0-9_]+$/.test(updatedModel.identifier)
    );
  };

  const correlationKeyOptions = () => {
    return correlationKeys.results.map((key: any) => {
      return <SelectItem value={key.identifier} text={key.identifier} />;
    });
  };

  const onCorrelationKeySelected = (event: any) => {
    correlationKeys.results.forEach((key: any) => {
      if (key.identifier === event.target.value) {
        console.log('Key updated', key);
        setCorrelationKey(key);
      }
    });
  };

  const retrievalExpressionFields = () => {
    console.log('Correlation Key', correlationKey, showCorrelations);
    if (correlationKey && showCorrelations) {
      const fields = correlationKey.properties.map((prop: any) => {
        const label = `Extraction Expression for ${prop}`;
        return (
          <TextInput
            id={prop}
            name={prop}
            invalid={identifierInvalid}
            labelText={label}
            defaultValue={prop}
//            onChange={}
          />
        );
      });
      return (
        <div className={'retrievalExpressionsForm'}>
          <h2>Retrieval Expressions:</h2>
          The body of the message should be a JSON object that includes these properties.  The value
          of each property will be extracted from the message and used to correlate the message to a
          running process.
          {fields}
        </div>
      )
    }
    return null;
  };

  const createMessageForm = () => {
    return (
      <Form onSubmit={onClose}>
        <Stack gap={5}>
          <TextInput
            id="message_name"
            name="message_name"
            placeholder="food_is_ready"
            invalidText='Minimum of 3 letters, please use only letters and underscores, ie "food_is_ready"'
            invalid={identifierInvalid}
            labelText="Message Name*"
            defaultValue={updatedModel.identifier}
            onChange={onMessageNameChange}
          />
          <Checkbox
            id="show_correlations"
            labelText="Correlate this message"
            checked={showCorrelations}
            helperText="Correlations are used to assure that messages are delivered only to those process
            instances that are related. For example a process instance that prepares food for table 12 would
            not receive a message about table 11, because it is CORRELATED to a specific table number."
          />
          <Select
            id="correlation_key"
            labelText="Select a correlation"
            onChange={onCorrelationKeySelected}
            visible={showCorrelations}
          >
            {correlationKeyOptions()}
          </Select>
          {retrievalExpressionFields()}
        </Stack>
      </Form>
    );
  };

  return (
    <Modal
      open={open}
      onRequestClose={onClose}
      modalHeading={`${messageModel.identifier}`}
      modalLabel="Details"
    >
      {createMessageForm()}
    </Modal>
  );
}
