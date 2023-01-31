import React from 'react';
import { FieldHelpProps } from '@rjsf/utils';
import FormHelperText from '@mui/material/FormHelperText';

/** The `FieldHelpTemplate` component renders any help desired for a field
 *
 * @param props - The `FieldHelpProps` to be rendered
 */
export default function FieldHelpTemplate(props: FieldHelpProps) {
  // ui:help is handled by helperText in all carbon widgets.
  // see BaseInputTemplate/BaseInputTemplate.tsx and
  // SelectWidget/SelectWidget.tsx
  return null;
}
