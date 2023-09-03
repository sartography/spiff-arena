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
  name: 'Registration',
  description: 'A simple registration form',
  schema: require('../../resources/json_schema_examples/registration-schema.json'), // eslint-disable-line global-require
  ui: require('../../resources/json_schema_examples/registration-uischema.json'), // eslint-disable-line global-require
});
// @ts-ignore
examples.push({
  name: 'Nested',
  description: 'Allow adding multiple entries to a single form.',
  schema: require('../../resources/json_schema_examples/nested-schema.json'), // eslint-disable-line global-require
  ui: require('../../resources/json_schema_examples/nested-uischema.json'), // eslint-disable-line global-require
});

type OwnProps = {
  onSelect: Function;
};

export default function ExamplesTable({ onSelect }: OwnProps) {
  function selectExample(index: number) {
    onSelect(examples[index].schema, examples[index].ui);
  }

  // Render the form in another div
  const rows: object[] = examples.map((example, index) => {
    return (
      <tr>
        <td>{example.name}</td>
        <td>{example.description}</td>
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
    <Table size='lg'>
      <TableHead>
        <TableRow>
          <TableHeader key="name" title="Name">
            Name
          </TableHeader>
          <TableHeader key="desc" title="Description">
            Description
          </TableHeader>
          <TableHeader key="load" title="Load">
            Load
          </TableHeader>
        </TableRow>
      </TableHead>
      <TableBody>{rows}</TableBody>
    </Table>
  );
}
