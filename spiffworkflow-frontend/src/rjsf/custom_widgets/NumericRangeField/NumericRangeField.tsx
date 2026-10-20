import {
  descriptionId,
  FieldProps,
  getTemplate,
  getUiOptions,
} from '@rjsf/utils';
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { getCommonAttributes } from '../../helpers';
import { FormattedNumberWidget } from '../../formEnhancements';
import {
  formatLocalizedNumber,
  resolveNumberLocale,
} from '../../localizedNumbers';

// Example jsonSchema - NOTE: the "min" and "max" properties are special names and must be used:
//    "compensation":{
//      "title": "Compensation (yearly), USD",
//      "type": "object",
//      "minimum": 0,
//      "maximum": 999999999999,
//      "properties": {
//        "min": {
//          "type": "number"
//        },
//        "max": {
//          "type": "number"
//        }
//      }
//    }
//
//  Example uiSchema:
//    "compensation": {
//      "ui:field": "numeric-range",
//      "ui:options": { "decimals": 2, "currency": "EUR" }
//    }
//
// Both inputs are formatted number widgets, so they follow the user's number
// notation and accept the same ui:options (locale, decimals, currency,
// allowNegative).

type RangeEnd = 'min' | 'max';

export default function NumericRangeField({
  schema,
  uiSchema,
  fieldPathId,
  disabled,
  readonly,
  onChange,
  onBlur,
  onFocus,
  autofocus,
  name,
  rawErrors = [],
  errorSchema,
  formData,
  registry,
  required,
}: FieldProps) {
  // Subscribing re-renders the bounds text when the user switches language.
  useTranslation();
  const commonAttributes = getCommonAttributes(
    name,
    schema,
    uiSchema,
    rawErrors,
  );

  const description = schema?.description || uiSchema?.['ui:description'];

  const uiOptions = getUiOptions(uiSchema || {});
  const DescriptionFieldTemplate = getTemplate(
    'DescriptionFieldTemplate',
    registry,
    uiOptions,
  );
  const rawNumberOptions = uiSchema?.['ui:options'];
  const numberOptions = useMemo(
    () => rawNumberOptions ?? {},
    [rawNumberOptions],
  );
  const locale = resolveNumberLocale(numberOptions.locale);

  const minNumber = schema.minimum;
  const maxNumber = schema.maximum;
  const hasBounds = minNumber !== undefined || maxNumber !== undefined;
  const formatBound = (bound: number | undefined, unbounded: string) =>
    bound === undefined ? unbounded : formatLocalizedNumber(bound, locale);

  const renderEnd = (end: RangeEnd) => {
    const endSchema = (schema as any).properties?.[end] ?? {};
    const helpText =
      end === 'min'
        ? `Min: ${formatBound(minNumber, '-∞')}`
        : `Max: ${formatBound(maxNumber, '∞')}`;
    return (
      <FormattedNumberWidget
        id={`${fieldPathId.$id}_${end}`}
        name={end}
        label={end === 'min' ? 'Minimum' : 'Maximum'}
        // The range bounds apply to both ends, which also lets a non-negative
        // range reject a minus sign.
        schema={{
          type: 'number',
          ...endSchema,
          minimum: minNumber,
          maximum: maxNumber,
        }}
        uiSchema={hasBounds ? { 'ui:help': helpText } : {}}
        options={numberOptions}
        value={formData?.[end]}
        onChange={(value: any) => onChange(value, [...fieldPathId.path, end])}
        onBlur={onBlur}
        onFocus={onFocus}
        disabled={disabled}
        readonly={readonly}
        autofocus={end === 'min' && autofocus}
        required={false}
        rawErrors={errorSchema?.[end]?.__errors ?? []}
        registry={registry}
      />
    );
  };

  return (
    <div className="numeric--range-field-wrapper">
      <div>
        <h5>
          {required
            ? commonAttributes.labelWithRequiredIndicator
            : commonAttributes.label}
        </h5>
        {description && (
          <div className="markdown-field-desc-text">
            <DescriptionFieldTemplate
              id={descriptionId(fieldPathId)}
              description={description}
              schema={schema}
              uiSchema={uiSchema}
              registry={registry}
            />
          </div>
        )}
      </div>
      <div className="numeric--range-field-inputs">
        {renderEnd('min')}
        {renderEnd('max')}
      </div>
      {commonAttributes.errorMessageForField && (
        <div className="error-message">
          {commonAttributes.errorMessageForField}
        </div>
      )}
      {commonAttributes.helperText && (
        <p className="numeric--range-field-help-text">
          {commonAttributes.helperText}
        </p>
      )}
    </div>
  );
}
