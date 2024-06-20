import React from 'react';
import {
  FormContextType,
  IconButtonProps,
  RJSFSchema,
  StrictRJSFSchema,
} from '@rjsf/utils';
import { Button } from '@carbon/react';
import { Add } from '@carbon/icons-react';

/** The `AddButton` renders a button that represent the `Add` action on a form
 */
export default function AddButton<
  T = any,
  S extends StrictRJSFSchema = RJSFSchema,
  F extends FormContextType = any,
>({ className, onClick, disabled, registry }: IconButtonProps<T, S, F>) {
  return (
    <Button
      iconType="info"
      kind="tertiary"
      size="sm"
      renderIcon={Add}
      title="Add"
      onClick={onClick}
      disabled={disabled}
      registry={registry}
    >
      Add new
    </Button>
  );
}
