import React from 'react';
import {
  DescriptionFieldProps,
  FormContextType,
  RJSFSchema,
  StrictRJSFSchema,
} from '@rjsf/utils';
import MDEditor from '@uiw/react-md-editor';
/** The `DescriptionField` is the template to use to render the description of a field
 *
 * @param props - The `DescriptionFieldProps` for this component
 */
export default function DescriptionField<
  T = any,
  S extends StrictRJSFSchema = RJSFSchema,
  F extends FormContextType = any,
>(props: DescriptionFieldProps<T, S, F>) {
  const { id, description } = props;
  if (!description) {
    return null;
  }
  if (typeof description === 'string') {
    return (
      //  const descriptionMarkdown =
      //  <span data-color-mode="light">
      //  </span>

      <p id={id} className="field-description" data-color-mode="light">
        <MDEditor.Markdown linkTarget="_blank" source={description} />
      </p>
    );
  }
  return (
    <div id={id} className="field-description">
      {description}
    </div>
  );
}
