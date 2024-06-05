import {
  canExpand,
  FormContextType,
  getTemplate,
  getUiOptions,
  ObjectFieldTemplateProps,
  ObjectFieldTemplatePropertyType,
  RJSFSchema,
  StrictRJSFSchema,
} from '@rjsf/utils';
import { Grid, Column } from '@carbon/react';

/* usage: add ui:layout to an object in the uiSchema
 *
 * If using ui:layout then ALL fields must be specified in the desired order.
 * The sm, md, and lg options match the Column options for Carbon theme. So they
 * specify how many grid columns the field takes up.
 *
 * Example uiSchema:
 *
 * {
 *   "ui:layout": [
 *     {
 *       "firstName": {
 *         "sm": 2,
 *         "md": 2,
 *         "lg": 4
 *       },
 *       "lastName": {
 *         "sm": 2,
 *         "md": 2,
 *         "lg": 4
 *       }
 *     },
 *     {
 *       "user": {}
 *     },
 *     {
 *       "details": {}
 *     }
 *   ],
 *   "user": {
 *     "ui:layout": [
 *       { "username": {}, "password": {} }
 *     ]
 *   }
 * }
 */

// these are not used by rjsf but can be passed in if calling this template directly.
type customProps = {
  defaultSm: number;
  defaultMd: number;
  defaultLg: number;
};

export default function ObjectFieldTemplate<
  T = any,
  S extends StrictRJSFSchema = RJSFSchema,
  F extends FormContextType = any,
>(
  props: ObjectFieldTemplateProps<T, S, F>,
  { defaultSm = 4, defaultMd = 8, defaultLg = 16 }: customProps,
) {
  const {
    description,
    disabled,
    formData,
    idSchema,
    onAddClick,
    properties,
    readonly,
    registry,
    required,
    schema,
    title,
    uiSchema,
  } = props;
  const options = getUiOptions<T, S, F>(uiSchema);
  const TitleFieldTemplate = getTemplate<'TitleFieldTemplate', T, S, F>(
    'TitleFieldTemplate',
    registry,
    options,
  );
  const DescriptionFieldTemplate = getTemplate<
    'DescriptionFieldTemplate',
    T,
    S,
    F
  >('DescriptionFieldTemplate', registry, options);
  // Button templates are not overridden in the uiSchema
  const {
    ButtonTemplates: { AddButton },
  } = registry.templates;

  const layout = (uiSchema as any)['ui:layout'];
  const schemaToUse = schema as any;

  let innerElements = null;

  if (layout) {
    innerElements = layout.map((row: any) => {
      const numberOfColumns = Object.keys(row).length;
      return (
        <Grid condensed fullWidth>
          {Object.keys(row).map((name) => {
            const element: any = properties.find((property: any) => {
              return property.name === name;
            });
            if (schemaToUse.properties[name]) {
              const { sm, md, lg } = row[name];
              return (
                <Column
                  className="side-by-side-column"
                  sm={sm || Math.floor(defaultSm / numberOfColumns)}
                  md={md || Math.floor(defaultMd / numberOfColumns)}
                  lg={lg || Math.floor(defaultLg / numberOfColumns)}
                >
                  {element.content}
                </Column>
              );
            }
            return (
              <div className="error-message">
                {`ERROR: '${name}' property was specified in the UI Schema's ui:layout, but property does not exist in the json schema.`}
              </div>
            );
          })}
        </Grid>
      );
    });
  } else {
    innerElements = properties.map(
      (prop: ObjectFieldTemplatePropertyType) => prop.content,
    );
  }

  return (
    <fieldset id={idSchema.$id}>
      {(options.title || title) && (
        <TitleFieldTemplate
          id={`${idSchema.$id}__title`}
          title={options.title || title}
          required={required}
          schema={schema}
          uiSchema={uiSchema}
          registry={registry}
        />
      )}
      {(options.description || description) && (
        <DescriptionFieldTemplate
          id={`${idSchema.$id}__description`}
          description={options.description || description!}
          schema={schema}
          uiSchema={uiSchema}
          registry={registry}
        />
      )}

      {innerElements}

      {canExpand<T, S, F>(schema, uiSchema, formData) && (
        <AddButton
          className="object-property-expand"
          onClick={onAddClick(schema)}
          disabled={disabled || readonly}
          uiSchema={uiSchema}
          registry={registry}
        />
      )}
    </fieldset>
  );
}
