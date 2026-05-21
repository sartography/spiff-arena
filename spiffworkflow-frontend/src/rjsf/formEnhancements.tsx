import { FieldProps, WidgetProps } from '@rjsf/utils';
import { TextInput } from '@carbon/react';
import { useEffect, useState } from 'react';
import { getCommonAttributes } from './helpers';

const isPlainObject = (value: any) =>
  value !== null && typeof value === 'object' && !Array.isArray(value);

const schemaTypes = (schema: any): string[] => {
  const type = schema?.type;
  return Array.isArray(type) ? type : type ? [type] : [];
};

const schemaHasNumericType = (schema: any) => {
  const types = schemaTypes(schema);
  return types.includes('number') || types.includes('integer');
};

const schemaHasIntegerType = (schema: any) =>
  schemaTypes(schema).includes('integer');

const decimalLimitFor = (schema: any, options: any = {}) => {
  if (typeof options.decimals === 'number') {
    return Math.max(0, options.decimals);
  }
  if (schemaHasIntegerType(schema)) {
    return 0;
  }
  return null;
};

const allowsNegative = (schema: any, options: any = {}) => {
  if (typeof options.allowNegative === 'boolean') {
    return options.allowNegative;
  }
  return !(typeof schema?.minimum === 'number' && schema.minimum >= 0);
};

export const stripNumberFormatting = (
  value: any,
  schema: any = {},
  options: any = {},
) => {
  if (value === null || value === undefined) {
    return '';
  }

  const rawValue = String(value).replace(/,/g, '').trim();
  if (!rawValue) {
    return '';
  }

  const negative = allowsNegative(schema, options) && rawValue.startsWith('-');
  const body = rawValue.replace(/-/g, '');
  const [integerPart, ...decimalParts] = body.split('.');
  const integerDigits = integerPart.replace(/\D/g, '');
  const limit = decimalLimitFor(schema, options);
  const decimalDigits = decimalParts.join('').replace(/\D/g, '');

  let normalized = `${negative ? '-' : ''}${integerDigits}`;
  if (limit !== 0 && body.includes('.')) {
    const limitedDecimalDigits =
      limit === null ? decimalDigits : decimalDigits.slice(0, limit);
    normalized = `${normalized}.${limitedDecimalDigits}`;
  }

  if (normalized === '-' || normalized === '-.') {
    return normalized;
  }
  if (normalized === '.' || normalized === '') {
    return body.includes('.') ? '0.' : '';
  }
  if (normalized.startsWith('-.')) {
    return `-0${normalized.slice(1)}`;
  }
  return normalized;
};

export const formatNumberForDisplay = (
  value: any,
  schema: any = {},
  options: any = {},
) => {
  const normalized = stripNumberFormatting(value, schema, options);
  if (!normalized || normalized === '-' || normalized === '-.') {
    return normalized;
  }

  const negative = normalized.startsWith('-');
  const unsigned = negative ? normalized.slice(1) : normalized;
  const [integerPart, decimalPart] = unsigned.split('.');
  const integerWithCommas = (integerPart || '0').replace(
    /\B(?=(\d{3})+(?!\d))/g,
    ',',
  );
  const decimalSuffix = normalized.includes('.') ? `.${decimalPart ?? ''}` : '';

  return `${negative ? '-' : ''}${integerWithCommas}${decimalSuffix}`;
};

export const coerceFormattedNumberValue = (
  value: any,
  schema: any = {},
  options: any = {},
) => {
  const normalized = stripNumberFormatting(value, schema, options);
  if (!normalized || normalized === '-' || normalized === '-.') {
    return undefined;
  }

  if (!schemaHasNumericType(schema)) {
    return normalized;
  }

  const numericValue = Number(normalized);
  return Number.isFinite(numericValue) ? numericValue : undefined;
};

const toNumber = (value: any) => {
  if (value === null || value === undefined || value === '') {
    return 0;
  }
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : 0;
  }
  const numericValue = Number(stripNumberFormatting(value));
  return Number.isFinite(numericValue) ? numericValue : 0;
};

const getByPath = (data: any, path: string) => {
  if (!path) {
    return data;
  }
  return path.split('.').reduce((current, part) => {
    if (current === null || current === undefined) {
      return undefined;
    }
    return current[part];
  }, data);
};

type ExpressionToken = {
  type: 'identifier' | 'number' | 'operator';
  value: string | number;
};

const tokenizeExpression = (expression: string): ExpressionToken[] => {
  const tokens: ExpressionToken[] = [];
  let index = 0;

  while (index < expression.length) {
    const char = expression[index];
    if (/\s/.test(char)) {
      index += 1;
      continue;
    }
    if ('()+-*/'.includes(char)) {
      tokens.push({ type: 'operator', value: char });
      index += 1;
      continue;
    }

    const numberMatch = expression
      .slice(index)
      .match(/^(?:\d+(?:\.\d*)?|\.\d+)/);
    if (numberMatch) {
      tokens.push({ type: 'number', value: Number(numberMatch[0]) });
      index += numberMatch[0].length;
      continue;
    }

    const identifierMatch = expression
      .slice(index)
      .match(/^(?:\$\.|[A-Za-z_])[$A-Za-z0-9_.]*/);
    if (identifierMatch) {
      tokens.push({ type: 'identifier', value: identifierMatch[0] });
      index += identifierMatch[0].length;
      continue;
    }

    throw new Error(
      `Unsupported token in calculated expression near "${expression.slice(index)}"`,
    );
  }

  return tokens;
};

export const evaluateCalculatedExpression = (
  expression: string,
  localData: any = {},
  rootData: any = localData,
) => {
  const tokens = tokenizeExpression(expression ?? '');
  let index = 0;

  const peek = () => tokens[index];
  const consume = (expectedValue?: string) => {
    const token = tokens[index];
    if (!token || (expectedValue && token.value !== expectedValue)) {
      throw new Error(`Expected "${expectedValue}" in calculated expression`);
    }
    index += 1;
    return token;
  };
  const identifierValue = (identifier: string) => {
    const path = identifier.startsWith('$.') ? identifier.slice(2) : identifier;
    const localValue = identifier.startsWith('$.')
      ? undefined
      : getByPath(localData, path);
    if (localValue !== undefined) {
      return toNumber(localValue);
    }
    return toNumber(getByPath(rootData, path));
  };

  let parseExpression: () => number;

  const parseFactor = (): number => {
    const token = peek();
    if (!token) {
      throw new Error('Unexpected end of calculated expression');
    }

    if (token.value === '+') {
      consume('+');
      return parseFactor();
    }
    if (token.value === '-') {
      consume('-');
      return -parseFactor();
    }
    if (token.value === '(') {
      consume('(');
      const value = parseExpression();
      consume(')');
      return value;
    }
    if (token.type === 'number') {
      consume();
      return token.value as number;
    }
    if (token.type === 'identifier') {
      consume();
      return identifierValue(token.value as string);
    }

    throw new Error(
      `Unexpected token "${token.value}" in calculated expression`,
    );
  };

  const parseTerm = () => {
    let value = parseFactor();
    while (peek()?.value === '*' || peek()?.value === '/') {
      const operator = consume().value;
      const right = parseFactor();
      value = operator === '*' ? value * right : value / right;
    }
    return value;
  };

  parseExpression = () => {
    let value = parseTerm();
    while (peek()?.value === '+' || peek()?.value === '-') {
      const operator = consume().value;
      const right = parseTerm();
      value = operator === '+' ? value + right : value - right;
    }
    return value;
  };

  if (!tokens.length) {
    return undefined;
  }
  const result = parseExpression();
  if (index !== tokens.length) {
    throw new Error(
      `Unexpected token "${tokens[index].value}" in calculated expression`,
    );
  }
  return Number.isFinite(result) ? result : undefined;
};

const cloneData = (value: any): any => {
  if (Array.isArray(value)) {
    return value.map(cloneData);
  }
  if (isPlainObject(value)) {
    return Object.fromEntries(
      Object.entries(value).map(([key, childValue]) => [
        key,
        cloneData(childValue),
      ]),
    );
  }
  return value;
};

const uiOptions = (uiSchema: any) => uiSchema?.['ui:options'] ?? {};

const hasCalculatedDescendant = (
  schema: any = {},
  uiSchema: any = {},
): boolean => {
  if (uiSchema?.['ui:field'] === 'calculated') {
    return true;
  }
  if (schema?.items) {
    return hasCalculatedDescendant(schema.items, uiSchema?.items ?? {});
  }
  return Object.keys(schema?.properties ?? {}).some((propertyKey) =>
    hasCalculatedDescendant(
      schema.properties[propertyKey],
      uiSchema?.[propertyKey] ?? {},
    ),
  );
};

const applyPrecision = (value: any, options: any) => {
  if (value === undefined) {
    return value;
  }
  if (typeof options.decimals !== 'number') {
    return value;
  }
  return Number(value.toFixed(Math.max(0, options.decimals)));
};

const applyCalculatedFieldsInPlace = (
  schema: any = {},
  uiSchema: any = {},
  data: any,
  rootData: any,
) => {
  if (!schema || !uiSchema || data === null || data === undefined) {
    return;
  }

  if (Array.isArray(data) && schema.items) {
    data.forEach((item) =>
      applyCalculatedFieldsInPlace(
        schema.items,
        uiSchema.items ?? {},
        item,
        rootData,
      ),
    );
    return;
  }

  if (!isPlainObject(data)) {
    return;
  }

  Object.entries(schema.properties ?? {}).forEach(
    ([propertyKey, propertySchema]) => {
      const propertySchemaToUse = propertySchema as any;
      const propertyUiSchema = uiSchema[propertyKey] ?? {};
      const options = uiOptions(propertyUiSchema);

      if (propertyUiSchema['ui:field'] === 'calculated') {
        if (typeof options.expression === 'string') {
          data[propertyKey] = applyPrecision(
            evaluateCalculatedExpression(options.expression, data, rootData),
            options,
          );
        }
        return;
      }

      if (propertySchemaToUse?.items && Array.isArray(data[propertyKey])) {
        applyCalculatedFieldsInPlace(
          propertySchemaToUse,
          propertyUiSchema,
          data[propertyKey],
          rootData,
        );
        return;
      }

      if (propertySchemaToUse?.properties) {
        if (
          data[propertyKey] === undefined &&
          hasCalculatedDescendant(propertySchemaToUse, propertyUiSchema)
        ) {
          data[propertyKey] = {};
        }
        applyCalculatedFieldsInPlace(
          propertySchemaToUse,
          propertyUiSchema,
          data[propertyKey],
          rootData,
        );
      }
    },
  );
};

export const applyCalculatedFields = (
  schema: any = {},
  uiSchema: any = {},
  formData: any = {},
) => {
  if (!hasCalculatedDescendant(schema, uiSchema)) {
    return formData ?? {};
  }

  const nextFormData = cloneData(formData ?? {});
  applyCalculatedFieldsInPlace(schema, uiSchema, nextFormData, nextFormData);
  return nextFormData;
};

export function FormattedNumberWidget({
  id,
  value,
  required,
  disabled,
  readonly,
  autofocus,
  onBlur,
  onChange,
  onFocus,
  options,
  placeholder,
  schema,
  uiSchema,
  label,
  rawErrors = [],
}: WidgetProps) {
  const widgetOptions = options ?? {};
  const commonAttributes = getCommonAttributes(
    label || '',
    schema,
    uiSchema,
    rawErrors,
  );
  const [displayValue, setDisplayValue] = useState(() =>
    formatNumberForDisplay(value, schema, widgetOptions),
  );

  useEffect(() => {
    setDisplayValue(formatNumberForDisplay(value, schema, widgetOptions));
  }, [schema, value, widgetOptions]);

  const handleChange = (event: any) => {
    const nextDisplayValue = formatNumberForDisplay(
      event.currentTarget.value,
      schema,
      widgetOptions,
    );
    setDisplayValue(nextDisplayValue);
    if (!disabled && !readonly) {
      onChange(
        coerceFormattedNumberValue(nextDisplayValue, schema, widgetOptions),
      );
    }
  };

  return (
    <TextInput
      id={id}
      type="text"
      labelText={
        required
          ? commonAttributes.labelWithRequiredIndicator
          : commonAttributes.label
      }
      disabled={disabled}
      readOnly={readonly}
      value={displayValue}
      onBlur={(event: any) =>
        onBlur?.(
          id,
          coerceFormattedNumberValue(
            event.currentTarget.value,
            schema,
            widgetOptions,
          ),
        )
      }
      onChange={handleChange}
      onFocus={(event: any) => onFocus?.(id, event.currentTarget.value)}
      invalid={commonAttributes.invalid}
      invalidText={commonAttributes.errorMessageForField}
      helperText={commonAttributes.helperText}
      placeholder={placeholder}
      autoFocus={autofocus}
      inputMode={schemaHasIntegerType(schema) ? 'numeric' : 'decimal'}
    />
  );
}

const formatCalculatedFieldValue = (value: any, options: any = {}) => {
  if (value === undefined || value === null) {
    return '';
  }
  if (options.format === 'currency') {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: options.currency ?? 'USD',
      minimumFractionDigits: options.decimals ?? 2,
      maximumFractionDigits: options.decimals ?? 2,
    }).format(value);
  }
  if (options.format === 'number' || typeof value === 'number') {
    return formatNumberForDisplay(value, { type: 'number' }, options);
  }
  return String(value);
};

export function CalculatedField({
  id,
  disabled,
  formData,
  label,
  rawErrors = [],
  required,
  schema,
  uiSchema,
}: FieldProps) {
  const commonAttributes = getCommonAttributes(
    label || '',
    schema,
    uiSchema,
    rawErrors,
  );
  const options = uiOptions(uiSchema);

  return (
    <TextInput
      id={id}
      type="text"
      labelText={
        required
          ? commonAttributes.labelWithRequiredIndicator
          : commonAttributes.label
      }
      disabled={disabled}
      readOnly
      value={formatCalculatedFieldValue(formData, options)}
      invalid={commonAttributes.invalid}
      invalidText={commonAttributes.errorMessageForField}
      helperText={commonAttributes.helperText}
    />
  );
}
