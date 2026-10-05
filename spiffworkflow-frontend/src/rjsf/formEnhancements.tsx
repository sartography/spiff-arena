import { FieldProps, WidgetProps } from '@rjsf/utils';
import { InputAdornment, TextField } from '@mui/material';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { getCommonAttributes } from './helpers';
import {
  allowsNegative,
  currencyAffixFor,
  decimalLimitFor,
  formatLocalizedNumber,
  parseLocalizedNumber,
  resolveNumberLocale,
  schemaHasIntegerType,
} from './localizedNumbers';

const isPlainObject = (value: any) =>
  value !== null && typeof value === 'object' && !Array.isArray(value);

const normalizeNumberInput = (
  value: any,
  schema: any = {},
  options: any = {},
) => {
  if (value === null || value === undefined) {
    return { normalized: '', hasInvalidFractionalPart: false };
  }

  const rawValue = String(value).replace(/,/g, '').trim();
  if (!rawValue) {
    return { normalized: '', hasInvalidFractionalPart: false };
  }

  const negative = allowsNegative(schema, options) && rawValue.startsWith('-');
  const body = rawValue.replace(/-/g, '');
  const [integerPart, ...decimalParts] = body.split('.');
  const integerDigits = integerPart.replace(/\D/g, '');
  const limit = decimalLimitFor(schema, options);
  const decimalDigits = decimalParts.join('').replace(/\D/g, '');
  const hasInvalidFractionalPart = limit === 0 && decimalDigits.length > 0;

  let normalized = `${negative ? '-' : ''}${integerDigits}`;
  if (body.includes('.')) {
    const limitedDecimalDigits =
      limit === null || limit === 0
        ? decimalDigits
        : decimalDigits.slice(0, limit);
    normalized = `${normalized}.${limitedDecimalDigits}`;
  }

  if (normalized === '-' || normalized === '-.') {
    return { normalized, hasInvalidFractionalPart };
  }
  if (normalized === '.' || normalized === '') {
    return {
      normalized: body.includes('.') ? '0.' : '',
      hasInvalidFractionalPart,
    };
  }
  if (normalized.startsWith('-.')) {
    return {
      normalized: `-0${normalized.slice(1)}`,
      hasInvalidFractionalPart,
    };
  }

  return { normalized, hasInvalidFractionalPart };
};

export const stripNumberFormatting = (
  value: any,
  schema: any = {},
  options: any = {},
) => {
  return normalizeNumberInput(value, schema, options).normalized;
};

/**
 * Formats a stored value for display in the locale from `options.locale`
 * (unset or "auto" follows the user's language).
 */
export const formatNumberForDisplay = (value: any, options: any = {}) =>
  formatLocalizedNumber(value, resolveNumberLocale(options.locale), options);

/**
 * Converts text typed in the field's locale to the value stored in form data:
 * a number for numeric schemas or a dot-decimal string for string schemas.
 * Empty and invalid text both yield undefined.
 */
export const coerceFormattedNumberValue = (
  text: any,
  schema: any = {},
  options: any = {},
) => {
  const parsed = parseLocalizedNumber(
    text,
    resolveNumberLocale(options.locale),
    schema,
    options,
  );
  return parsed.status === 'valid' ? parsed.value : undefined;
};

export type FormattedNumberFormContext = {
  invalidFormattedNumbers?: Map<string, string>;
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

const countCalculatedDescendants = (
  schema: any = {},
  uiSchema: any = {},
): number => {
  const currentNodeCount = uiSchema?.['ui:field'] === 'calculated' ? 1 : 0;
  if (schema?.items) {
    return (
      currentNodeCount +
      countCalculatedDescendants(schema.items, uiSchema?.items ?? {})
    );
  }
  return (
    currentNodeCount +
    Object.keys(schema?.properties ?? {}).reduce(
      (count, propertyKey) =>
        count +
        countCalculatedDescendants(
          schema.properties[propertyKey],
          uiSchema?.[propertyKey] ?? {},
        ),
      0,
    )
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
): boolean => {
  if (!schema || !uiSchema || data === null || data === undefined) {
    return false;
  }

  if (Array.isArray(data) && schema.items) {
    return data.reduce(
      (changed, item) =>
        applyCalculatedFieldsInPlace(
          schema.items,
          uiSchema.items ?? {},
          item,
          rootData,
        ) || changed,
      false,
    );
  }

  if (!isPlainObject(data)) {
    return false;
  }

  return Object.entries(schema.properties ?? {}).reduce<boolean>(
    (changed, [propertyKey, propertySchema]) => {
      const propertySchemaToUse = propertySchema as any;
      const propertyUiSchema = uiSchema[propertyKey] ?? {};
      const options = uiOptions(propertyUiSchema);

      if (propertyUiSchema['ui:field'] === 'calculated') {
        if (typeof options.expression === 'string') {
          const nextValue = applyPrecision(
            evaluateCalculatedExpression(options.expression, data, rootData),
            options,
          );
          if (!Object.is(data[propertyKey], nextValue)) {
            data[propertyKey] = nextValue;
            return true;
          }
        }
        return changed;
      }

      if (propertySchemaToUse?.items && Array.isArray(data[propertyKey])) {
        return (
          applyCalculatedFieldsInPlace(
            propertySchemaToUse,
            propertyUiSchema,
            data[propertyKey],
            rootData,
          ) || changed
        );
      }

      if (propertySchemaToUse?.properties) {
        let nextChanged = changed;
        if (
          data[propertyKey] === undefined &&
          hasCalculatedDescendant(propertySchemaToUse, propertyUiSchema)
        ) {
          data[propertyKey] = {};
          nextChanged = true;
        }
        return (
          applyCalculatedFieldsInPlace(
            propertySchemaToUse,
            propertyUiSchema,
            data[propertyKey],
            rootData,
          ) || nextChanged
        );
      }

      return changed;
    },
    false,
  );
};

export type ApplyCalculatedFieldsResult = {
  formState: any;
  stabilized: boolean;
  warning?: string;
};

export const applyCalculatedFields = (
  schema: any = {},
  uiSchema: any = {},
  formData: any = {},
): ApplyCalculatedFieldsResult => {
  if (!hasCalculatedDescendant(schema, uiSchema)) {
    return {
      formState: formData ?? {},
      stabilized: true,
    };
  }

  const nextFormData = cloneData(formData ?? {});
  const maxPasses = countCalculatedDescendants(schema, uiSchema) + 1;
  let changed = false;

  for (let pass = 0; pass < maxPasses; pass += 1) {
    changed = applyCalculatedFieldsInPlace(
      schema,
      uiSchema,
      nextFormData,
      nextFormData,
    );
    if (!changed) {
      break;
    }
  }

  if (changed) {
    const warning =
      'Could not calculate value. Check expression for circular dependencies.';
    return {
      formState: nextFormData,
      stabilized: false,
      warning,
    };
  }

  return {
    formState: nextFormData,
    stabilized: true,
  };
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
  registry,
}: WidgetProps) {
  // Subscribing re-renders the widget when the user switches language.
  const { t } = useTranslation();
  const widgetOptions = useMemo(() => options ?? {}, [options]);
  const locale = resolveNumberLocale(widgetOptions.locale);
  const commonAttributes = getCommonAttributes(
    label || '',
    schema,
    uiSchema,
    rawErrors,
  );
  const [displayValue, setDisplayValue] = useState(() =>
    formatLocalizedNumber(value, locale, widgetOptions),
  );
  const [focused, setFocused] = useState(false);
  // Invalid text is stored as undefined, so the echoed value must not
  // overwrite what the user is still typing.
  const lastEmittedValue = useRef<any>(value);
  const lastLocale = useRef(locale);

  useEffect(() => {
    const changedExternally = !Object.is(value, lastEmittedValue.current);
    const localeChanged = lastLocale.current !== locale;
    lastLocale.current = locale;
    const hasStoredValue = value !== undefined && value !== null;
    if (!changedExternally && !(localeChanged && !focused && hasStoredValue)) {
      return;
    }
    lastEmittedValue.current = value;
    setDisplayValue(formatLocalizedNumber(value, locale, widgetOptions));
  }, [focused, locale, value, widgetOptions]);

  const parsed = parseLocalizedNumber(
    displayValue,
    locale,
    schema,
    widgetOptions,
  );
  const isInvalid = parsed.status === 'invalid';
  const decimalLimit = decimalLimitFor(schema, widgetOptions);
  const exampleDecimals = decimalLimit ?? 2;
  const example = formatLocalizedNumber(
    exampleDecimals > 0
      ? `1234567.${'89'.padEnd(exampleDecimals, '0').slice(0, exampleDecimals)}`
      : '1234567',
    locale,
    { decimals: exampleDecimals },
  );
  const invalidMessage = t('invalid_number_format', { example });
  const fieldLabel = commonAttributes.label;
  const invalidRegistry = (
    registry?.formContext as FormattedNumberFormContext | undefined
  )?.invalidFormattedNumbers;
  const blocksSubmission = isInvalid && !disabled && !readonly;

  useEffect(() => {
    if (!invalidRegistry) {
      return undefined;
    }
    if (blocksSubmission) {
      invalidRegistry.set(id, `${fieldLabel}: ${invalidMessage}`);
    } else {
      invalidRegistry.delete(id);
    }
    return () => {
      invalidRegistry.delete(id);
    };
  }, [blocksSubmission, fieldLabel, id, invalidMessage, invalidRegistry]);

  const handleChange = (event: any) => {
    const text = event.currentTarget.value;
    setDisplayValue(text);
    if (disabled || readonly) {
      return;
    }
    const nextValue = coerceFormattedNumberValue(text, schema, {
      ...widgetOptions,
      locale,
    });
    lastEmittedValue.current = nextValue;
    onChange(nextValue);
  };

  const handleBlur = (event: any) => {
    setFocused(false);
    const result = parseLocalizedNumber(
      event.currentTarget.value,
      locale,
      schema,
      widgetOptions,
    );
    if (result.status === 'valid') {
      setDisplayValue(
        formatLocalizedNumber(result.canonical, locale, widgetOptions),
      );
    }
    onBlur?.(id, result.status === 'valid' ? result.value : undefined);
  };

  const showInvalid = isInvalid && !focused;
  const currencyAffix = currencyAffixFor(widgetOptions.currency, locale);
  const adornment = currencyAffix ? (
    <InputAdornment position={currencyAffix.position}>
      {currencyAffix.symbol}
    </InputAdornment>
  ) : undefined;

  let helperText = commonAttributes.helperText;
  if (showInvalid) {
    helperText = invalidMessage;
  } else if (commonAttributes.invalid) {
    helperText = commonAttributes.errorMessageForField;
  }

  return (
    <TextField
      id={id}
      type="text"
      label={
        required
          ? commonAttributes.labelWithRequiredIndicator
          : commonAttributes.label
      }
      disabled={disabled}
      slotProps={{
        htmlInput: {
          readOnly: readonly,
          inputMode: schemaHasIntegerType(schema) ? 'numeric' : 'decimal',
          lang: locale,
        },
        input: adornment
          ? {
              [currencyAffix?.position === 'start'
                ? 'startAdornment'
                : 'endAdornment']: adornment,
            }
          : undefined,
      }}
      value={displayValue}
      onBlur={handleBlur}
      onChange={handleChange}
      onFocus={(event: any) => {
        setFocused(true);
        onFocus?.(id, event.currentTarget.value);
      }}
      error={commonAttributes.invalid || showInvalid}
      helperText={helperText}
      placeholder={placeholder}
      autoFocus={autofocus}
      fullWidth
    />
  );
}

const formatCalculatedFieldValue = (value: any, options: any = {}) => {
  if (value === undefined || value === null) {
    return '';
  }
  const locale = resolveNumberLocale(options.locale);
  if (options.format === 'currency') {
    try {
      return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: options.currency ?? 'USD',
        minimumFractionDigits: options.decimals ?? 2,
        maximumFractionDigits: options.decimals ?? 2,
      }).format(value);
    } catch {
      // An invalid currency code falls back to plain number formatting.
    }
  }
  if (
    options.format === 'number' ||
    options.format === 'currency' ||
    typeof value === 'number'
  ) {
    return formatLocalizedNumber(value, locale, options);
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
  // Subscribing re-renders the field when the user switches language.
  useTranslation();
  const commonAttributes = getCommonAttributes(
    label || '',
    schema,
    uiSchema,
    rawErrors,
  );
  const options = uiOptions(uiSchema);

  return (
    <TextField
      id={id}
      type="text"
      label={
        required
          ? commonAttributes.labelWithRequiredIndicator
          : commonAttributes.label
      }
      disabled={disabled}
      slotProps={{ htmlInput: { readOnly: true } }}
      value={formatCalculatedFieldValue(formData, options)}
      error={commonAttributes.invalid}
      helperText={
        commonAttributes.invalid
          ? commonAttributes.errorMessageForField
          : commonAttributes.helperText
      }
      fullWidth
    />
  );
}
