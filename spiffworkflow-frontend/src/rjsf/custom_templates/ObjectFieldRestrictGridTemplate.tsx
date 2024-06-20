import {
  FormContextType,
  ObjectFieldTemplateProps,
  RJSFSchema,
  StrictRJSFSchema,
} from '@rjsf/utils';
import ObjectFieldTemplate from '../carbon_theme/ObjectFieldTemplate';

/*
 * Returns the ObjectFieldTemplate but with restricted column count for the carbon grid.
 * Only affects rjsf object field type with the "ui:layout".
 */

export default function ObjectFieldRestrictedGridTemplate<
  T = any,
  S extends StrictRJSFSchema = RJSFSchema,
  F extends FormContextType = any,
>(props: ObjectFieldTemplateProps<T, S, F>) {
  return ObjectFieldTemplate(props, {
    defaultSm: 4,
    defaultMd: 5,
    defaultLg: 8,
  });
}
