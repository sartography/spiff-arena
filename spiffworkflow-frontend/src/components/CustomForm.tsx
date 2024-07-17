import validator from '@rjsf/validator-ajv8';
import { ComponentType, ReactNode, useEffect, useRef } from 'react';
import { RegistryFieldsType } from '@rjsf/utils';
import { Button } from '@carbon/react';
import { Form as MuiForm } from '@rjsf/mui';
import { Form as CarbonForm } from '../rjsf/carbon_theme';
import { DATE_RANGE_DELIMITER } from '../config';
import DateRangePickerWidget from '../rjsf/custom_widgets/DateRangePicker/DateRangePickerWidget';
import TypeaheadWidget from '../rjsf/custom_widgets/TypeaheadWidget/TypeaheadWidget';
import MarkDownFieldWidget from '../rjsf/custom_widgets/MarkDownFieldWidget/MarkDownFieldWidget';
import NumericRangeField from '../rjsf/custom_widgets/NumericRangeField/NumericRangeField';
import ObjectFieldRestrictedGridTemplate from '../rjsf/custom_templates/ObjectFieldRestrictGridTemplate';
import { matchNumberRegex } from '../helpers';

enum DateCheckType {
  minimum = 'minimum',
  maximum = 'maximum',
}

type OwnProps = {
  id: string;
  key: string;
  formData: any;
  schema: any;
  uiSchema: any;
  className?: string;
  disabled?: boolean;
  onChange?: any;
  onSubmit?: any;
  children?: ReactNode;
  noValidate?: boolean;
  restrictedWidth?: boolean;
  submitButtonText?: string;
  reactJsonSchemaForm?: string;
  hideSubmitButton?: boolean;
  bpmnEvent?: any;
};

const withProps = <P extends object>(
  Component: ComponentType<P>,
  customProps: Partial<P>,
) =>
  function CustomComponent(props: P) {
    // eslint-disable-next-line react/jsx-props-no-spreading
    return <Component {...props} {...customProps} />;
  };

export default function CustomForm({
  id,
  key,
  formData,
  className,
  schema,
  uiSchema,
  disabled = false,
  onChange,
  onSubmit,
  children,
  noValidate = false,
  restrictedWidth = false,
  submitButtonText,
  reactJsonSchemaForm = 'carbon',
  hideSubmitButton = false,
  bpmnEvent,
}: OwnProps) {
  let reactJsonSchemaFormTheme = reactJsonSchemaForm;
  if ('ui:theme' in uiSchema) {
    if (uiSchema['ui:theme'] === 'carbon') {
      reactJsonSchemaFormTheme = 'carbon';
    } else if (uiSchema['ui:theme'] === 'mui') {
      reactJsonSchemaFormTheme = 'mui';
    } else {
      console.error(
        `Unsupported theme: ${uiSchema['ui:theme']}. Defaulting to mui`,
      );
      reactJsonSchemaFormTheme = 'mui';
    }
  }

  const customTypeaheadWidget = withProps(TypeaheadWidget, {
    reactJsonSchemaFormTheme,
  });

  // set in uiSchema using the "ui:widget" key for a property
  const rjsfWidgets = {
    'date-range': DateRangePickerWidget,
    markdown: MarkDownFieldWidget,
    typeahead: customTypeaheadWidget,
  };

  // set in uiSchema using the "ui:field" key for a property
  const rjsfFields: RegistryFieldsType = {
    'numeric-range': NumericRangeField,
  };

  const rjsfTemplates: any = {};
  if (restrictedWidth && reactJsonSchemaFormTheme === 'carbon') {
    rjsfTemplates.ObjectFieldTemplate = ObjectFieldRestrictedGridTemplate;
  }

  const formatDateString = (dateString?: string) => {
    let dateObject = new Date();
    if (dateString) {
      dateObject = new Date(dateString);
    }
    return dateObject.toISOString().split('T')[0];
  };

  const checkFieldComparisons = (
    checkType: DateCheckType,
    formDataToCheck: any,
    propertyKey: string,
    dateCheck: string,
    formattedDateString: string,
    errors: any,
    jsonSchema: any,
  ) => {
    // field format:
    //    field:[field_name_to_use]
    //
    // if field is a range:
    //    field:[field_name_to_use]:[start or end]
    //
    // defaults to "start" in all cases
    const [_, fieldIdentifierToCompareWith, startOrEnd] = dateCheck.split(':');
    if (!(fieldIdentifierToCompareWith in formDataToCheck)) {
      errors[propertyKey].addError(
        `was supposed to be compared against '${fieldIdentifierToCompareWith}' but it either doesn't have a value or does not exist`,
      );
      return;
    }

    const rawDateToCompareWith = formDataToCheck[fieldIdentifierToCompareWith];
    if (!rawDateToCompareWith) {
      errors[propertyKey].addError(
        `was supposed to be compared against '${fieldIdentifierToCompareWith}' but that field did not have a value`,
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

    let fieldToCompareWithTitle = fieldIdentifierToCompareWith;
    if (
      fieldIdentifierToCompareWith in jsonSchema.properties &&
      jsonSchema.properties[fieldIdentifierToCompareWith].title
    ) {
      fieldToCompareWithTitle =
        jsonSchema.properties[fieldIdentifierToCompareWith].title;
    }

    const dateStringToCompareWith = formatDateString(dateToCompareWith);
    if (checkType === 'minimum') {
      if (dateStringToCompareWith > formattedDateString) {
        errors[propertyKey].addError(
          `must be equal to or greater than '${fieldToCompareWithTitle}'`,
        );
      }
      // best NOT to merge this with nested if statement in case we add more or move code around
      // eslint-disable-next-line sonarjs/no-collapsible-if
    } else if (checkType === 'maximum') {
      if (dateStringToCompareWith < formattedDateString) {
        errors[propertyKey].addError(
          `must be equal to or less than '${fieldToCompareWithTitle}'`,
        );
      }
    }
  };

  const runDateChecks = (
    checkType: DateCheckType,
    dateChecks: string[],
    formDataToCheck: any,
    propertyKey: string,
    formattedDateString: string,
    errors: any,
    jsonSchema: any,
  ) => {
    dateChecks.forEach((mdc: string) => {
      if (mdc === 'today') {
        const dateTodayString = formatDateString();
        if (checkType === 'minimum') {
          if (dateTodayString > formattedDateString) {
            errors[propertyKey].addError('must be today or after');
          }
          // best NOT to merge this with nested if statement in case we add more or move code around
          // eslint-disable-next-line sonarjs/no-collapsible-if
        } else if (checkType === 'maximum') {
          if (dateTodayString < formattedDateString) {
            errors[propertyKey].addError('must be today or before');
          }
        }
      } else if (mdc.startsWith('field:')) {
        checkFieldComparisons(
          checkType,
          formDataToCheck,
          propertyKey,
          mdc,
          formattedDateString,
          errors,
          jsonSchema,
        );
      }
    });
  };

  const checkDateValidations = (
    checkType: DateCheckType,
    formDataToCheck: any,
    propertyKey: string,
    propertyMetadata: any,
    errors: any,
    jsonSchema: any,
  ) => {
    // can be either "today" or another field
    let dateString = formDataToCheck[propertyKey];
    if (dateString) {
      if (typeof dateString === 'string') {
        // in the case of date ranges, just take the start date and check that
        [dateString] = dateString.split(DATE_RANGE_DELIMITER);
      }
      const formattedDateString = formatDateString(dateString);
      let dateChecks = null;
      if (checkType === 'minimum') {
        dateChecks = propertyMetadata.minimumDate.split(',');
      } else if (checkType === 'maximum') {
        dateChecks = propertyMetadata.maximumDate.split(',');
      }
      runDateChecks(
        checkType,
        dateChecks,
        formDataToCheck,
        propertyKey,
        formattedDateString,
        errors,
        jsonSchema,
      );
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
    uiSchemaPassedIn?: any,
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
        `must have required property '${propertyKey}'`,
      );
    }
  };

  const checkJsonField = (
    formDataToCheck: any,
    propertyKey: string,
    errors: any,
    _jsonSchema: any,
    _uiSchemaPassedIn?: any,
  ) => {
    if (propertyKey in formDataToCheck) {
      try {
        JSON.parse(formDataToCheck[propertyKey]);
      } catch (e) {
        errors[propertyKey].addError(`has invalid JSON: ${e}`);
      }
    }
  };

  const checkNumericRange = (
    formDataToCheck: any,
    propertyKey: string,
    errors: any,
    jsonSchema: any,
    _uiSchemaPassedIn?: any,
    // eslint-disable-next-line sonarjs/cognitive-complexity
  ) => {
    if (
      jsonSchema.required &&
      jsonSchema.required.includes(propertyKey) &&
      (formDataToCheck[propertyKey].min === undefined ||
        formDataToCheck[propertyKey].max === undefined)
    ) {
      errors[propertyKey].addError('must have valid Minimum and Maximum');
    }
    if (formDataToCheck[propertyKey].min !== undefined) {
      if (
        !formDataToCheck[propertyKey].min.toString().match(matchNumberRegex)
      ) {
        errors[propertyKey].addError('must have valid numbers');
      }
      if (
        formDataToCheck[propertyKey].min <
        jsonSchema.properties[propertyKey].minimum
      ) {
        errors[propertyKey].addError(
          `must have min greater than or equal to ${jsonSchema.properties[propertyKey].minimum}`,
        );
      }
      if (
        formDataToCheck[propertyKey].min >
        jsonSchema.properties[propertyKey].maximum
      ) {
        errors[propertyKey].addError(
          `must have min less than or equal to ${jsonSchema.properties[propertyKey].maximum}`,
        );
      }
    }
    if (formDataToCheck[propertyKey].max !== undefined) {
      if (
        !formDataToCheck[propertyKey].max.toString().match(matchNumberRegex)
      ) {
        errors[propertyKey].addError('must have valid numbers');
      }
      if (
        formDataToCheck[propertyKey].max <
        jsonSchema.properties[propertyKey].minimum
      ) {
        errors[propertyKey].addError(
          `must have max greater than or equal to ${jsonSchema.properties[propertyKey].minimum}`,
        );
      }
      if (
        formDataToCheck[propertyKey].max >
        jsonSchema.properties[propertyKey].maximum
      ) {
        errors[propertyKey].addError(
          `must have max less than or equal to ${jsonSchema.properties[propertyKey].maximum}`,
        );
      }
    }
    if (formDataToCheck[propertyKey].min > formDataToCheck[propertyKey].max) {
      errors[propertyKey].addError(`must have min less than or equal to max`);
    }
  };

  const checkCharacterCounter = (
    formDataToCheck: any,
    propertyKey: string,
    errors: any,
    jsonSchema: any,
    _uiSchemaPassedIn?: any,
  ) => {
    if (
      jsonSchema.required &&
      jsonSchema.required.includes(propertyKey) &&
      (formDataToCheck[propertyKey] === undefined ||
        formDataToCheck[propertyKey] === '')
    ) {
      errors[propertyKey].addError(
        `must have required property '${propertyKey}'`,
      );
    }
  };

  const checkFieldsWithCustomValidations = (
    jsonSchema: any,
    formDataToCheck: any,
    errors: any,
    uiSchemaPassedIn?: any,
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
          checkDateValidations(
            DateCheckType.minimum,
            formDataToCheck,
            propertyKey,
            propertyMetadata,
            errors,
            jsonSchemaToUse,
          );
        }
        if ('maximumDate' in propertyMetadata) {
          checkDateValidations(
            DateCheckType.maximum,
            formDataToCheck,
            propertyKey,
            propertyMetadata,
            errors,
            jsonSchemaToUse,
          );
        }

        if (propertyMetadata.type === 'boolean') {
          checkBooleanField(
            formDataToCheck,
            propertyKey,
            errors,
            jsonSchemaToUse,
            currentUiSchema,
          );
        }
        if (
          currentUiSchema &&
          'ui:options' in currentUiSchema &&
          currentUiSchema['ui:options'].validateJson === true
        ) {
          checkJsonField(
            formDataToCheck,
            propertyKey,
            errors,
            jsonSchemaToUse,
            currentUiSchema,
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
            currentUiSchema,
          );
        }

        if (
          currentUiSchema &&
          'ui:field' in currentUiSchema &&
          currentUiSchema['ui:field'] === 'character-counter'
        ) {
          checkCharacterCounter(
            formDataToCheck,
            propertyKey,
            errors,
            jsonSchemaToUse,
            currentUiSchema,
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
              currentUiSchema,
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

  let childrenToUse = children;
  const submitButtonRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    if (bpmnEvent && submitButtonText) {
      const triggerSaveEvent = (event: any) => {
        if (submitButtonRef.current) {
          submitButtonRef.current.click();
        }
        event.stopPropagation();
      };

      bpmnEvent.eventBus.on('spiff.message.save', triggerSaveEvent);

      return () => {
        bpmnEvent.eventBus.off('spiff.message.save', triggerSaveEvent);
      };
    }
    return undefined;
  }, [bpmnEvent, submitButtonText]);

  if (submitButtonText) {
    childrenToUse = (
      <Button
        type="submit"
        ref={submitButtonRef}
        id="submit-button"
        disabled={disabled}
        style={{ display: hideSubmitButton ? 'none' : 'unset' }}
      >
        {submitButtonText}
      </Button>
    );
  }

  const formProps = {
    id,
    key,
    className,
    disabled,
    formData,
    onChange,
    onSubmit,
    schema,
    uiSchema,
    widgets: rjsfWidgets,
    validator,
    customValidate,
    noValidate,
    fields: rjsfFields,
    templates: rjsfTemplates,
    omitExtraData: true,
  };
  if (reactJsonSchemaFormTheme === 'carbon') {
    // eslint-disable-next-line react/jsx-props-no-spreading
    return <CarbonForm {...formProps}>{childrenToUse}</CarbonForm>;
  }

  if (reactJsonSchemaFormTheme === 'mui') {
    // eslint-disable-next-line react/jsx-props-no-spreading
    return <MuiForm {...formProps}>{childrenToUse}</MuiForm>;
  }

  console.error(`Unsupported form type: ${reactJsonSchemaFormTheme}`);
  return null;
}
