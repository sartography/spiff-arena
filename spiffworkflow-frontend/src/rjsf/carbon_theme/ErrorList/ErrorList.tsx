import { ErrorListProps } from '@rjsf/utils';
// @ts-ignore
import { Tag } from '@carbon/react';

function ErrorList({ errors }: ErrorListProps) {
  if (errors) {
    return (
      <Tag type="red" size="md" title="Fix validation issues">
        Some fields are invalid. Please correct them before submitting the form.
      </Tag>
    );
  }
  return null;
}

export default ErrorList;
