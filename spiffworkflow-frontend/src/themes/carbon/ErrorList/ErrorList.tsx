import { ErrorListProps } from '@rjsf/utils';
// @ts-ignore
import { Tag } from '@carbon/react';

function ErrorList({ errors }: ErrorListProps) {
  if (errors) {
    return (
      <Tag type="red" size="md" title="Fill Required Fields">
        Please fill out required fields
      </Tag>
    );
  }
  return null;
}

export default ErrorList;
