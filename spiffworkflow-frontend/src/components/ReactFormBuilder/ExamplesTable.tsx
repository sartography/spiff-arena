import React from 'react';
import {
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  Button,
} from '@carbon/react';
import { JsonSchemaExample } from '../../interfaces';

const examples: JsonSchemaExample[] = [];
examples.push({
  schema: require('../../resources/json_schema_examples/text-schema.json'), // eslint-disable-line global-require
  ui: require('../../resources/json_schema_examples/text-uischema.json'), // eslint-disable-line global-require
  data: {},
});
examples.push({
  schema: require('../../resources/json_schema_examples/textarea-schema.json'), // eslint-disable-line global-require
  ui: require('../../resources/json_schema_examples/textarea-uischema.json'), // eslint-disable-line global-require
  data: {},
});
examples.push({
  schema: require('../../resources/json_schema_examples/checkbox-schema.json'), // eslint-disable-line global-require
  ui: {},
  data: {},
});
examples.push({
  schema: require('../../resources/json_schema_examples/date-schema.json'), // eslint-disable-line global-require
  ui: require('../../resources/json_schema_examples/date-uischema.json'), // eslint-disable-line global-require
  data: {},
});
examples.push({
  schema: require('../../resources/json_schema_examples/dropdown-schema.json'), // eslint-disable-line global-require
  ui: {},
  data: require('../../resources/json_schema_examples/dropdown-exampledata.json'), // eslint-disable-line global-require
});
examples.push({
  schema: require('../../resources/json_schema_examples/multiple-choice-schema.json'), // eslint-disable-line global-require
  ui: require('../../resources/json_schema_examples/multiple-choice-uischema.json'), // eslint-disable-line global-require
  data: {},
});
examples.push({
  schema: require('../../resources/json_schema_examples/password-schema.json'), // eslint-disable-line global-require
  ui: require('../../resources/json_schema_examples/password-uischema.json'), // eslint-disable-line global-require
  data: {},
});
examples.push({
  schema: require('../../resources/json_schema_examples/nested-schema.json'), // eslint-disable-line global-require
  ui: {},
  data: {},
});
examples.push({
  schema: require('../../resources/json_schema_examples/typeahead-schema.json'), // eslint-disable-line global-require
  ui: require('../../resources/json_schema_examples/typeahead-uischema.json'), // eslint-disable-line global-require
  data: {},
});

type OwnProps = {
  onSelect: Function;
};

export default function ExamplesTable({ onSelect }: OwnProps) {
  function selectExample(index: number) {
    onSelect(examples[index].schema, examples[index].ui, examples[index].data);
  }

  // Render the form in another div
  const rows: object[] = examples.map((example, index) => {
    return (
      <tr>
        <td>{example.schema.title}</td>
        <td>{example.schema.description}</td>
        <td>
          <Button
            kind="secondary"
            size="sm"
            onClick={() => selectExample(index)}
          >
            Load
          </Button>
        </td>
      </tr>
    );
  });

  return (
    <Table size="lg">
      <TableHead>
        <TableRow>
          <TableHeader key="name" title="Name">
            Name
          </TableHeader>
          <TableHeader key="desc" title="Description">
            Description
          </TableHeader>
          <TableHeader key="load" title="Load">
            Insert
          </TableHeader>
        </TableRow>
      </TableHead>
      <TableBody>{rows}</TableBody>
    </Table>
  );
}
