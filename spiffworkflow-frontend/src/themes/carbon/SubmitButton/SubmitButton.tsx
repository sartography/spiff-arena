import React from 'react';
// import Box from '@mui/material/Box';
// @ts-ignore
import { Button } from '@carbon/react';
import { SubmitButtonProps, getSubmitButtonOptions } from '@rjsf/utils';

// const SubmitButton: React.ComponentType<SubmitButtonProps> = (props) => {
function SubmitButton(props: SubmitButtonProps) {
  const { uiSchema } = props;
  const {
    submitText,
    norender,
    props: submitButtonProps,
  } = getSubmitButtonOptions(uiSchema);
  if (norender) {
    return null;
  }
  return (
    <Button
      className="react-json-schema-form-submit-button"
      type="submit"
      // eslint-disable-next-line react/jsx-props-no-spreading
      {...submitButtonProps}
    >
      {submitText}
    </Button>
  );
}

export default SubmitButton;
