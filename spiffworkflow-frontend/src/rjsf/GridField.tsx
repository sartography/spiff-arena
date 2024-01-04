import { ObjectFieldTemplateProps } from '@rjsf/utils';
import { Grid, Column } from '@carbon/react';

export default function ObjectFieldTemplate({
  description,
  disabled,
  formContext,
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
  ...otherProps
}: ObjectFieldTemplateProps) {
  // return (
  //   <div>
  //     {title}
  //     {description}
  //     {properties.map((element) => (
  //       <div className="property-wrapper-2">{element.content}</div>
  //     ))}
  //   </div>
  // );
  // console.log('schema', schema);
  console.log('properties', properties);
  // console.log('otherProps', otherProps);
  // console.log('registry', registry);
  console.log('idSchema', idSchema);
  const layout = (uiSchema as any)['ui:layout'];
  const schemaToUse = schema as any;
  return (
    <div>
      {title}
      {description}
      {layout.map((row: any, index: any) => {
        return (
          <Grid condensed fullWidth>
            {Object.keys(row).map((name, index) => {
              const element: any = properties.find((property: any) => {
                return property.name === name;
              });
              // const element = schemaToUse.properties[name];
              // console.log('element', element);
              // console.log('element', element);
              const currentSchema = element.content.props.schema;
              // const { ...rowProps } = row[name];
              if (schemaToUse.properties[name]) {
                return (
                  <Column>
                    {currentSchema.properties
                      ? ObjectFieldTemplate(element.content.props)
                      : element.content}
                  </Column>
                );
              }
              console.error(
                `'${name}' property was specified in ui:layout but it does not exist in the jsonschema.`
              );
            })}
          </Grid>
        );
      })}
    </div>
  );
}

// // Originally from https://github.com/audibene-labs/react-jsonschema-form-layout/blob/master/src/index.js
//
// import React from 'react';
// import ObjectField from 'react-jsonschema-form/lib/components/fields/ObjectField';
// import { retrieveSchema } from 'react-jsonschema-form/lib/utils';
// // import { Col } from 'react-bootstrap';
//
// export default class GridField extends ObjectField {
//   state = { firstName: 'hasldf' };
//
//   render() {
//     const {
//       uiSchema,
//       errorSchema,
//       idSchema,
//       required,
//       disabled,
//       readonly,
//       onBlur,
//       formData,
//     } = this.props;
//     const { definitions, fields, formContext } = this.props.registry;
//     const { SchemaField, TitleField, DescriptionField } = fields;
//     const schema = retrieveSchema(this.props.schema, definitions);
//     const title = schema.title === undefined ? '' : schema.title;
//
//     const layout = uiSchema['ui:layout'];
//
//     return (
//       <fieldset>
//         {title ? (
//           <TitleField
//             id={`${idSchema.$id}__title`}
//             title={title}
//             required={required}
//             formContext={formContext}
//           />
//         ) : null}
//         {schema.description ? (
//           <DescriptionField
//             id={`${idSchema.$id}__description`}
//             description={schema.description}
//             formContext={formContext}
//           />
//         ) : null}
//         {layout.map((row, index) => {
//           return (
//             <div className="row" key={index}>
//               {Object.keys(row).map((name, index) => {
//                 const { doShow, ...rowProps } = row[name];
//                 let style = {};
//                 if (doShow && !doShow({ formData })) {
//                   style = { display: 'none' };
//                 }
//                 if (schema.properties[name]) {
//                   return (
//                     <Col {...rowProps} key={index} style={style}>
//                       <SchemaField
//                         name={name}
//                         required={this.isRequired(name)}
//                         schema={schema.properties[name]}
//                         uiSchema={uiSchema[name]}
//                         errorSchema={errorSchema[name]}
//                         idSchema={idSchema[name]}
//                         formData={formData[name]}
//                         onChange={this.onPropertyChange(name)}
//                         onBlur={onBlur}
//                         registry={this.props.registry}
//                         disabled={disabled}
//                         readonly={readonly}
//                       />
//                     </Col>
//                   );
//                 } else {
//                   const { render, ...rowProps } = row[name];
//                   function UIComponent() {
//                     return null;
//                   }
//
//                   if (render) {
//                     UIComponent = render;
//                   }
//
//                   return (
//                     <Col {...rowProps} key={index} style={style}>
//                       <UIComponent
//                         name={name}
//                         formData={formData}
//                         errorSchema={errorSchema}
//                         uiSchema={uiSchema}
//                         schema={schema}
//                         registry={this.props.registry}
//                       />
//                     </Col>
//                   );
//                 }
//               })}
//             </div>
//           );
//         })}
//       </fieldset>
//     );
//   }
// }
