import validator from '@rjsf/validator-ajv8';
import { ReactNode } from 'react';
import { RegistryFieldsType } from '@rjsf/utils';
import { Form } from '../rjsf/carbon_theme';
import { DATE_RANGE_DELIMITER } from '../config';
import DateRangePickerWidget from '../rjsf/custom_widgets/DateRangePicker/DateRangePickerWidget';
import TypeaheadWidget from '../rjsf/custom_widgets/TypeaheadWidget/TypeaheadWidget';
import MarkDownFieldWidget from '../rjsf/custom_widgets/MarkDownFieldWidget/MarkDownFieldWidget';
import NumericRangeField from '../rjsf/custom_widgets/NumericRangeField/NumericRangeField';

type OwnProps = {
  id: string;
  formData: any;
  schema: any;
  uiSchema: any;

  disabled?: boolean;
  onChange?: any;
  onSubmit?: any;
  children?: ReactNode;
  noValidate?: boolean;
};

export default function CustomForm({
  id,
  formData,
  schema,
  uiSchema,
  disabled = false,
  onChange,
  onSubmit,
  children,
  noValidate = false,
}: OwnProps) {
  // set in uiSchema using the "ui:widget" key for a property
  const rjsfWidgets = {
    'date-range': DateRangePickerWidget,
    markdown: MarkDownFieldWidget,
    typeahead: TypeaheadWidget,
  };

  // set in uiSchema using the "ui:field" key for a property
  const fields: RegistryFieldsType = {
    'numeric-range': NumericRangeField,
  };

  const formatDateString = (dateString?: string) => {
    let dateObject = new Date();
    if (dateString) {
      dateObject = new Date(dateString);
    }
    return dateObject.toISOString().split('T')[0];
  };

  const checkFieldComparisons = (
    formDataToCheck: any,
    propertyKey: string,
    minimumDateCheck: string,
    formattedDateString: string,
    errors: any,
    jsonSchema: any
  ) => {
    // field format:
    //    field:[field_name_to_use]
    //
    // if field is a range:
    //    field:[field_name_to_use]:[start or end]
    //
    // defaults to "start" in all cases
    const [_, fieldIdentifierToCompareWith, startOrEnd] =
      minimumDateCheck.split(':');
    if (!(fieldIdentifierToCompareWith in formDataToCheck)) {
      errors[propertyKey].addError(
        `was supposed to be compared against '${fieldIdentifierToCompareWith}' but it either doesn't have a value or does not exist`
      );
      return;
    }

    const rawDateToCompareWith = formDataToCheck[fieldIdentifierToCompareWith];
    if (!rawDateToCompareWith) {
      errors[propertyKey].addError(
        `was supposed to be compared against '${fieldIdentifierToCompareWith}' but that field did not have a value`
      );
      return;
    }

    const [startDate, endDate] =
      rawDateToCompareWith.split(DATE_RANGE_DELIMITER);
    let dateToCompareWith = startDate;
    if (startOrEnd && startOrEnd === 'end') {
      dateToCompareWith = endDate;
    }

    if (!dateToCompareWith) {
      const errorMessage = `was supposed to be compared against '${[
        fieldIdentifierToCompareWith,
        startOrEnd,
      ].join(':')}' but that field did not have a value`;
      errors[propertyKey].addError(errorMessage);
      return;
    }

    const dateStringToCompareWith = formatDateString(dateToCompareWith);
    if (dateStringToCompareWith > formattedDateString) {
      let fieldToCompareWithTitle = fieldIdentifierToCompareWith;
      if (
        fieldIdentifierToCompareWith in jsonSchema.properties &&
        jsonSchema.properties[fieldIdentifierToCompareWith].title
      ) {
        fieldToCompareWithTitle =
          jsonSchema.properties[fieldIdentifierToCompareWith].title;
      }
      errors[propertyKey].addError(
        `must be equal to or greater than '${fieldToCompareWithTitle}'`
      );
    }
  };

  const checkMinimumDate = (
    formDataToCheck: any,
    propertyKey: string,
    propertyMetadata: any,
    errors: any,
    jsonSchema: any
  ) => {
    // can be either "today" or another field
    let dateString = formDataToCheck[propertyKey];
    if (dateString) {
      if (typeof dateString === 'string') {
        // in the case of date ranges, just take the start date and check that
        [dateString] = dateString.split(DATE_RANGE_DELIMITER);
      }
      const formattedDateString = formatDateString(dateString);
      const minimumDateChecks = propertyMetadata.minimumDate.split(',');
      minimumDateChecks.forEach((mdc: string) => {
        if (mdc === 'today') {
          const dateTodayString = formatDateString();
          if (dateTodayString > formattedDateString) {
            errors[propertyKey].addError('must be today or after');
          }
        } else if (mdc.startsWith('field:')) {
          checkFieldComparisons(
            formDataToCheck,
            propertyKey,
            mdc,
            formattedDateString,
            errors,
            jsonSchema
          );
        }
      });
    }
  };

  // a required boolean field (checkbox) with default value of false
  // will not automatically fail validation. only undefined values will
  // trigger the validation by default so force it. this is to support things
  // like "I have read the EULA" type checkbox on a form.
  const checkBooleanField = (
    formDataToCheck: any,
    propertyKey: string,
    errors: any,
    jsonSchema: any,
    uiSchemaPassedIn?: any
  ) => {
    // this validation only applies to checkboxes,
    // other forms of booleans are validated differently
    if (
      uiSchemaPassedIn &&
      'ui:widget' in uiSchemaPassedIn &&
      uiSchemaPassedIn['ui:widget'] !== 'checkbox'
    ) {
      return;
    }
    if (
      jsonSchema.required &&
      jsonSchema.required.includes(propertyKey) &&
      formDataToCheck[propertyKey] !== true
    ) {
      // keep this error the same as the default message
      errors[propertyKey].addError(
        `must have required property '${propertyKey}'`
      );
    }
  };

  const checkNumericRange = (
    formDataToCheck: any,
    propertyKey: string,
    errors: any,
    _jsonSchema: any,
    _uiSchemaPassedIn?: any
  ) => {
    if (formDataToCheck[propertyKey].min > formDataToCheck[propertyKey].max) {
      errors[propertyKey].addError(
        `must have min less than max on numeric range`
      );
    }
  };

  const checkFieldsWithCustomValidations = (
    jsonSchema: any,
    formDataToCheck: any,
    errors: any,
    uiSchemaPassedIn?: any
    // eslint-disable-next-line sonarjs/cognitive-complexity
  ) => {
    // if the jsonSchema has an items attribute then assume the element itself
    // doesn't have a custom validation but it's children could so use that
    const jsonSchemaToUse =
      'items' in jsonSchema ? jsonSchema.items : jsonSchema;

    let uiSchemaToUse = uiSchemaPassedIn;
    if (!uiSchemaToUse) {
      uiSchemaToUse = uiSchema;
    }
    if ('items' in uiSchemaToUse) {
      uiSchemaToUse = uiSchemaToUse.items;
    }

    if ('properties' in jsonSchemaToUse) {
      Object.keys(jsonSchemaToUse.properties).forEach((propertyKey: string) => {
        const propertyMetadata = jsonSchemaToUse.properties[propertyKey];
        let currentUiSchema: any = null;
        if (propertyKey in uiSchemaToUse) {
          currentUiSchema = uiSchemaToUse[propertyKey];
        }
        if ('minimumDate' in propertyMetadata) {
          checkMinimumDate(
            formDataToCheck,
            propertyKey,
            propertyMetadata,
            errors,
            jsonSchemaToUse
          );
        }

        if (propertyMetadata.type === 'boolean') {
          checkBooleanField(
            formDataToCheck,
            propertyKey,
            errors,
            jsonSchemaToUse,
            currentUiSchema
          );
        }

        if (
          currentUiSchema &&
          'ui:field' in currentUiSchema &&
          currentUiSchema['ui:field'] === 'numeric-range'
        ) {
          checkNumericRange(
            formDataToCheck,
            propertyKey,
            errors,
            jsonSchemaToUse,
            currentUiSchema
          );
        }

        // recurse through all nested properties as well
        let formDataToSend = formDataToCheck[propertyKey];
        if (formDataToSend) {
          if (formDataToSend.constructor.name !== 'Array') {
            formDataToSend = [formDataToSend];
          }
          formDataToSend.forEach((item: any, index: number) => {
            let errorsToSend = errors[propertyKey];
            if (index in errorsToSend) {
              errorsToSend = errorsToSend[index];
            }
            checkFieldsWithCustomValidations(
              propertyMetadata,
              item,
              errorsToSend,
              currentUiSchema
            );
          });
        }
      });
    }
    return errors;
  };

  const customValidate = (formDataToCheck: any, errors: any) => {
    return checkFieldsWithCustomValidations(schema, formDataToCheck, errors);
  };

  return (
    <Form
      id={id}
      disabled={disabled}
      formData={formData}
      onChange={onChange}
      onSubmit={onSubmit}
      schema={schema}
      uiSchema={uiSchema}
      widgets={rjsfWidgets}
      validator={validator}
      customValidate={customValidate}
      noValidate={noValidate}
      fields={fields}
      omitExtraData
    >
      {children}
    </Form>
  );
}
