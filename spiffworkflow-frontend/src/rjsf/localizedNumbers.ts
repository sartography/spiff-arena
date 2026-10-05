import i18next from '../i18n';

export const DEFAULT_NUMBER_LOCALE = 'en-US';
export const AUTO_NUMBER_LOCALE = 'auto';

const isUsableLocale = (candidate: unknown): candidate is string => {
  if (typeof candidate !== 'string' || !candidate.trim()) {
    return false;
  }
  try {
    return Intl.NumberFormat.supportedLocalesOf([candidate]).length > 0;
  } catch {
    return false;
  }
};

/**
 * Resolves the locale used to parse and display a numeric form value.
 *
 * An explicit BCP 47 tag pins the field. Otherwise this follows the user's
 * language rather than i18next.resolvedLanguage: the resolved language is the
 * loaded translation, so a user whose language has no Arena translation would
 * otherwise be forced into en-US number notation.
 */
export const resolveNumberLocale = (requestedLocale?: unknown): string => {
  const candidates = [
    requestedLocale === AUTO_NUMBER_LOCALE ? undefined : requestedLocale,
    i18next.language,
    typeof navigator === 'undefined' ? undefined : navigator.language,
  ];
  const locale = candidates.find(isUsableLocale);
  return locale ?? DEFAULT_NUMBER_LOCALE;
};

type NumberSymbols = {
  decimal: string;
  group: string;
  groupEquivalents: string[];
  minusSigns: string[];
};

const WHITESPACE_GROUP_SYMBOLS = [' ', '\u00a0', '\u202f'];
const APOSTROPHE_GROUP_SYMBOLS = ["'", '\u2019'];

const integerFormatter = (locale: string, useGrouping?: 'always') =>
  new Intl.NumberFormat(locale, {
    numberingSystem: 'latn',
    maximumFractionDigits: 0,
    ...(useGrouping ? { useGrouping } : {}),
  } as Intl.NumberFormatOptions);

export const getNumberSymbols = (locale: string): NumberSymbols => {
  const parts = new Intl.NumberFormat(locale, {
    numberingSystem: 'latn',
    useGrouping: true,
  }).formatToParts(-12345.6);
  const partValue = (type: string, fallback: string) =>
    parts.find((part) => part.type === type)?.value ?? fallback;
  const decimal = partValue('decimal', '.');
  const group = partValue('group', decimal === ',' ? '.' : ',');
  let groupEquivalents = [group];
  if (WHITESPACE_GROUP_SYMBOLS.includes(group)) {
    groupEquivalents = WHITESPACE_GROUP_SYMBOLS;
  } else if (APOSTROPHE_GROUP_SYMBOLS.includes(group)) {
    groupEquivalents = APOSTROPHE_GROUP_SYMBOLS;
  }
  const minusSigns = Array.from(
    new Set(['-', '\u2212', partValue('minusSign', '-')]),
  );
  return { decimal, group, groupEquivalents, minusSigns };
};

const groupIntegerDigits = (digits: string, locale: string) =>
  integerFormatter(locale).format(BigInt(digits));

const acceptedGroupings = (digits: string, locale: string) => {
  const groupings = [digits, groupIntegerDigits(digits, locale)];
  try {
    // Locales such as es omit grouping for four-digit numbers by default but
    // still accept it, so "1.234" must be valid there.
    groupings.push(integerFormatter(locale, 'always').format(BigInt(digits)));
  } catch {
    // Engines without Intl.NumberFormat v3 reject useGrouping: 'always'.
  }
  return groupings;
};

const schemaTypes = (schema: any): string[] => {
  const type = schema?.type;
  return Array.isArray(type) ? type : type ? [type] : [];
};

export const schemaHasNumericType = (schema: any) => {
  const types = schemaTypes(schema);
  return types.includes('number') || types.includes('integer');
};

export const schemaHasIntegerType = (schema: any) =>
  schemaTypes(schema).includes('integer');

export const decimalLimitFor = (schema: any, options: any = {}) => {
  if (typeof options.decimals === 'number') {
    return Math.max(0, options.decimals);
  }
  if (schemaHasIntegerType(schema)) {
    return 0;
  }
  return null;
};

export const allowsNegative = (schema: any, options: any = {}) => {
  if (typeof options.allowNegative === 'boolean') {
    return options.allowNegative;
  }
  return !(typeof schema?.minimum === 'number' && schema.minimum >= 0);
};

export type ParsedLocalizedNumber =
  | { status: 'empty' }
  | { status: 'invalid' }
  | { status: 'valid'; canonical: string; value: number | string };

const CANONICAL_NUMBER = /^-?\d+(\.\d+)?$/;

/**
 * Strictly parses text typed in the given locale. Text that is not valid in
 * that locale is rejected rather than reinterpreted, so a separator from
 * another locale can never silently change a value's magnitude.
 */
export const parseLocalizedNumber = (
  text: unknown,
  locale: string,
  schema: any = {},
  options: any = {},
): ParsedLocalizedNumber => {
  if (text === null || text === undefined) {
    return { status: 'empty' };
  }
  let remaining = String(text).trim();
  if (!remaining) {
    return { status: 'empty' };
  }

  const symbols = getNumberSymbols(locale);
  const minusSign = symbols.minusSigns.find((sign) =>
    remaining.startsWith(sign),
  );
  const negative = minusSign !== undefined;
  if (minusSign) {
    remaining = remaining.slice(minusSign.length);
    if (!allowsNegative(schema, options)) {
      return { status: 'invalid' };
    }
  }

  const sections = remaining.split(symbols.decimal);
  if (sections.length > 2) {
    return { status: 'invalid' };
  }
  const [groupedInteger, fraction = ''] = sections;
  if (!/^\d*$/.test(fraction) || (!groupedInteger && !fraction)) {
    return { status: 'invalid' };
  }

  const integerText = symbols.groupEquivalents.reduce(
    (current, equivalent) => current.split(equivalent).join(symbols.group),
    groupedInteger,
  );
  const integerDigits = integerText.split(symbols.group).join('') || '0';
  if (!/^\d+$/.test(integerDigits)) {
    return { status: 'invalid' };
  }
  if (
    integerText &&
    !acceptedGroupings(integerDigits, locale).includes(integerText)
  ) {
    return { status: 'invalid' };
  }

  const limit = decimalLimitFor(schema, options);
  if (limit !== null && fraction.length > limit) {
    return { status: 'invalid' };
  }

  const normalizedInteger = BigInt(integerDigits).toString();
  const isZero = /^0*$/.test(normalizedInteger + fraction);
  const canonical = `${negative && !isZero ? '-' : ''}${normalizedInteger}${
    fraction ? `.${fraction}` : ''
  }`;

  if (!schemaHasNumericType(schema)) {
    return { status: 'valid', canonical, value: canonical };
  }
  const numericValue = Number(canonical);
  if (!Number.isFinite(numericValue)) {
    return { status: 'invalid' };
  }
  return { status: 'valid', canonical, value: numericValue };
};

const canonicalFromStoredValue = (value: unknown): string | null => {
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) {
      return null;
    }
    // Avoids exponent notation such as 1e21 or 1e-7 from String(value).
    return value.toLocaleString('en-US', {
      useGrouping: false,
      maximumFractionDigits: 20,
    });
  }
  if (typeof value === 'string' && CANONICAL_NUMBER.test(value)) {
    return value;
  }
  return null;
};

/**
 * Formats a stored value (a JSON number or a dot-decimal string) for display.
 * Anything else, such as invalid text from an older draft, is shown unchanged
 * so it is never silently rewritten.
 */
export const formatLocalizedNumber = (
  value: unknown,
  locale: string,
  options: any = {},
): string => {
  if (value === null || value === undefined || value === '') {
    return '';
  }
  const canonical = canonicalFromStoredValue(value);
  if (canonical === null) {
    return String(value);
  }
  const negative = canonical.startsWith('-');
  const [integerDigits, fraction = ''] = (
    negative ? canonical.slice(1) : canonical
  ).split('.');
  const decimals =
    typeof options.decimals === 'number' ? Math.max(0, options.decimals) : 0;
  const paddedFraction = fraction.padEnd(decimals, '0');
  const symbols = getNumberSymbols(locale);
  const minusSign = negative ? symbols.minusSigns[0] : '';
  const integerPart = groupIntegerDigits(integerDigits, locale);
  const fractionPart = paddedFraction
    ? `${symbols.decimal}${paddedFraction}`
    : '';
  return `${minusSign}${integerPart}${fractionPart}`;
};

export type CurrencyAffix = { position: 'start' | 'end'; symbol: string };

export const currencyAffixFor = (
  currency: unknown,
  locale: string,
): CurrencyAffix | null => {
  if (typeof currency !== 'string' || !currency.trim()) {
    return null;
  }
  try {
    const parts = new Intl.NumberFormat(locale, {
      style: 'currency',
      currency,
    }).formatToParts(1);
    const currencyIndex = parts.findIndex((part) => part.type === 'currency');
    const integerIndex = parts.findIndex((part) => part.type === 'integer');
    if (currencyIndex === -1) {
      return { position: 'end', symbol: currency };
    }
    return {
      position: currencyIndex < integerIndex ? 'start' : 'end',
      symbol: parts[currencyIndex].value,
    };
  } catch {
    return { position: 'end', symbol: currency };
  }
};
