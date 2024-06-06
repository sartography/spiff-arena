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
import textSchema from '../../resources/json_schema_examples/text-schema.json';
import textUiSchema from '../../resources/json_schema_examples/text-uischema.json';

import textareaSchema from '../../resources/json_schema_examples/textarea-schema.json';
import textareaUiSchema from '../../resources/json_schema_examples/textarea-uischema.json';

import dateSchema from '../../resources/json_schema_examples/date-schema.json';
import dateUiSchema from '../../resources/json_schema_examples/date-uischema.json';

import choiceSchema from '../../resources/json_schema_examples/multiple-choice-schema.json';
import choiceUiSchema from '../../resources/json_schema_examples/multiple-choice-uischema.json';

import passwordSchema from '../../resources/json_schema_examples/password-schema.json';
import passwordUiSchema from '../../resources/json_schema_examples/password-uischema.json';
import typeaheadSchema from '../../resources/json_schema_examples/typeahead-schema.json';
import typeaheadUiSchema from '../../resources/json_schema_examples/typeahead-uischema.json';

import checkboxSchema from '../../resources/json_schema_examples/checkbox-schema.json';
import dropdownSchema from '../../resources/json_schema_examples/dropdown-schema.json';
import dropdownData from '../../resources/json_schema_examples/dropdown-exampledata.json';
import nestedSchema from '../../resources/json_schema_examples/nested-schema.json';

const examples: JsonSchemaExample[] = [];

examples.push(
  {
    schema: textSchema,
    ui: textUiSchema,
    data: {},
  },
  {
    schema: textareaSchema,
    ui: textareaUiSchema,
    data: {},
  },
  {
    schema: checkboxSchema,
    ui: {},
    data: {},
  },
  {
    schema: dateSchema,
    ui: dateUiSchema,
    data: {},
  },
  {
    schema: dropdownSchema,
    ui: {},
    data: dropdownData,
  },
  {
    schema: choiceSchema,
    ui: choiceUiSchema,
    data: {},
  },
  {
    schema: passwordSchema,
    ui: passwordUiSchema,
    data: {},
  },
  {
    schema: nestedSchema,
    ui: {},
    data: {},
  },
  {
    schema: typeaheadSchema,
    ui: typeaheadUiSchema,
    data: {},
  },
);

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
          <Button kind="primary" size="sm" onClick={() => selectExample(index)}>
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
