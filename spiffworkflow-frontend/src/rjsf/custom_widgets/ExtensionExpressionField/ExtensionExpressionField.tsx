import { FieldProps, getUiOptions } from '@rjsf/utils';
import { CircularProgress } from '@mui/material';
import { Box, Stack, TextField, Typography } from '@mui/material';
import { KeyboardEvent, ReactNode, useEffect, useRef, useState } from 'react';
import HttpService from '../../../services/HttpService';

export type ExtensionExpressionResult = {
  status: 'valid' | 'invalid' | 'ambiguous';
  value?: Record<string, unknown>;
  assumptions?: string[];
  errors?: { code: string; message: string }[];
};

// ui:options keys that configure the field itself instead of flowing through
// to the extension resolver as extension_input.
const RESERVED_OPTION_KEYS = [
  'resolver',
  'idleMilliseconds',
  'examples',
  'emptyMessage',
];

const errorSchema = (message: string) => ({ __errors: [message] });

export type ExtensionExpressionExtraContext = {
  value: Record<string, unknown>;
  expression: string;
  disabled: boolean | undefined;
  readonly: boolean | undefined;
  $id: string;
  markValid: (value: Record<string, unknown>, assumptions?: string[]) => void;
  showError: (message: string) => void;
};

type ExtensionExpressionFieldProps = FieldProps<Record<string, unknown>> & {
  examples?: string;
  renderPreview?: (
    value: Record<string, unknown>,
    assumptions: string[],
  ) => ReactNode;
  renderExtra?: (context: ExtensionExpressionExtraContext) => ReactNode;
  initialize?: (
    value: Record<string, unknown>,
    timeZone: string,
  ) => Record<string, unknown> | undefined;
};

export default function ExtensionExpressionField({
  schema,
  uiSchema,
  fieldPathId,
  formData = {},
  onChange,
  onBlur,
  onFocus,
  disabled,
  readonly,
  label,
  examples,
  renderPreview,
  renderExtra,
  initialize,
}: ExtensionExpressionFieldProps) {
  const options = getUiOptions(uiSchema || {});
  const resolver = String(options.resolver || '');
  const idleMilliseconds = Number(options.idleMilliseconds || 500);
  const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
  const [expression, setExpression] = useState(
    typeof formData.expression === 'string' ? formData.expression : '',
  );
  const [assumptions, setAssumptions] = useState<string[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const requestRef = useRef<{ controller: AbortController; id: number } | null>(
    null,
  );
  const requestIdRef = useRef(0);
  const lastParsedRef = useRef<string | null>(
    typeof formData.expression === 'string' ? formData.expression : null,
  );
  const lastResultRef = useRef<{
    expression: string;
    status: 'valid' | 'invalid' | 'ambiguous';
  } | null>(null);
  const pendingParseRef = useRef(false);
  const submitAfterParseRef = useRef<HTMLButtonElement | null | undefined>(
    undefined,
  );
  const loadingRef = useRef(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const expressionRef = useRef(expression);
  expressionRef.current = expression;

  const emptyMessage = String(
    options.emptyMessage || 'Enter an expression.',
  );

  useEffect(() => {
    if (!initialize) {
      return;
    }
    const nextValue = initialize(formData, timeZone);
    if (nextValue) {
      onChange(
        nextValue,
        fieldPathId.path,
        undefined,
        fieldPathId.$id,
      );
    }
  }, [fieldPathId.$id, fieldPathId.path, formData, initialize, onChange, timeZone]);

  useEffect(
    () => () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      requestRef.current?.controller.abort();
    },
    [],
  );

  const emitError = (nextValue: Record<string, unknown>, errorMessage: string) => {
    setMessage(errorMessage);
    onChange(
      nextValue,
      fieldPathId.path,
      errorSchema(errorMessage),
      fieldPathId.$id,
    );
  };

  const parse = (value: string) => {
    lastParsedRef.current = value;
    const valueHasData = Object.entries(formData).some(
      ([key, entryValue]) =>
        key !== 'expression' &&
        entryValue !== undefined &&
        entryValue !== null &&
        entryValue !== '',
    );
    if (!value.trim()) {
      pendingParseRef.current = false;
      loadingRef.current = false;
      if (valueHasData) {
        // The expression was cleared but structured data remains. That is the
        // same state an existing record opens in, so it must stay submittable.
        setAssumptions([]);
        setMessage(null);
        lastResultRef.current = { expression: value, status: 'valid' };
        onChange(
          { ...formData, expression: value },
          fieldPathId.path,
          {},
          fieldPathId.$id,
        );
        maybeSubmitAfterParse();
        return;
      }
      emitError({ ...formData, expression: value }, emptyMessage);
      return;
    }
    if (!resolver.match(/^[a-zA-Z0-9][a-zA-Z0-9/_-]*$/)) {
      pendingParseRef.current = false;
      loadingRef.current = false;
      emitError(
        { ...formData, expression: value },
        'The configured expression resolver is invalid.',
      );
      return;
    }

    pendingParseRef.current = true;
    loadingRef.current = true;
    requestRef.current?.controller.abort();
    const controller = new AbortController();
    requestIdRef.current += 1;
    const requestId = requestIdRef.current;
    requestRef.current = { controller, id: requestId };
    setLoading(true);
    setMessage(null);

    const resolvedOptions = Intl.DateTimeFormat().resolvedOptions();
    const extensionInput: Record<string, unknown> = {};
    for (const [key, optionValue] of Object.entries(options)) {
      if (!RESERVED_OPTION_KEYS.includes(key)) {
        extensionInput[key] = optionValue;
      }
    }
    extensionInput.expression = value;
    extensionInput.reference_instant = new Date().toISOString();
    extensionInput.time_zone = resolvedOptions.timeZone;
    extensionInput.locale = resolvedOptions.locale;
    HttpService.makeCallToBackend({
      path: `/v1.0/extensions/${resolver}`,
      httpMethod: 'POST',
      signal: controller.signal,
      postBody: { extension_input: extensionInput },
      successCallback: (response: {
        task_data?: { result?: ExtensionExpressionResult };
      }) => {
        if (requestIdRef.current !== requestId) {
          return;
        }
        loadingRef.current = false;
        pendingParseRef.current = false;
        setLoading(false);
        const result = response.task_data?.result;
        if (result?.status === 'valid' && result.value) {
          setAssumptions(result.assumptions || []);
          setMessage(null);
          lastResultRef.current = { expression: value, status: 'valid' };
          onChange(result.value, fieldPathId.path, {}, fieldPathId.$id);
          maybeSubmitAfterParse();
          return;
        }
        // Invalid or ambiguous: drop any submit that was waiting on this
        // interpretation so stale values can never be submitted silently.
        submitAfterParseRef.current = undefined;
        lastResultRef.current = {
          expression: value,
          status: result?.status === 'ambiguous' ? 'ambiguous' : 'invalid',
        };
        const resultMessage =
          result?.errors?.[0]?.message ||
          'The expression could not be interpreted.';
        emitError({ ...formData, expression: value }, resultMessage);
      },
      failureCallback: (error: { name?: string }) => {
        if (
          requestIdRef.current !== requestId ||
          error?.name === 'AbortError'
        ) {
          return;
        }
        loadingRef.current = false;
        pendingParseRef.current = false;
        submitAfterParseRef.current = undefined;
        lastResultRef.current = { expression: value, status: 'invalid' };
        setLoading(false);
        emitError(
          { ...formData, expression: value },
          'The expression could not be checked. Your last valid values are unchanged.',
        );
      },
    });
  };

  const parseRef = useRef(parse);
  parseRef.current = parse;

  const scheduleParse = (value: string) => {
    pendingParseRef.current = true;
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    timerRef.current = setTimeout(() => parse(value), idleMilliseconds);
  };

  const maybeSubmitAfterParse = () => {
    if (submitAfterParseRef.current === undefined) {
      return;
    }
    const submitter = submitAfterParseRef.current;
    submitAfterParseRef.current = undefined;
    const form = rootRef.current?.closest('form');
    if (!form) {
      return;
    }
    // Let React flush the interpreted value into the form state first.
    setTimeout(() => form.requestSubmit(submitter ?? undefined), 0);
  };

  useEffect(() => {
    const handleSubmitCapture = (event: SubmitEvent) => {
      const form = rootRef.current?.closest('form');
      if (!form || event.target !== form) {
        return;
      }
      const lastResult = lastResultRef.current;
      if (
        !pendingParseRef.current &&
        (!lastResult ||
          lastResult.expression !== expressionRef.current ||
          lastResult.status === 'valid')
      ) {
        return;
      }
      if (pendingParseRef.current) {
        // A submit raced a scheduled or in-flight interpretation. Hold it
        // until the interpretation settles so recorded values always match
        // the submitted expression, then submit automatically.
        event.preventDefault();
        event.stopPropagation();
        submitAfterParseRef.current =
          (event.submitter as HTMLButtonElement | null) ?? null;
        if (timerRef.current) {
          clearTimeout(timerRef.current);
          timerRef.current = null;
        }
        if (!loadingRef.current) {
          parseRef.current(expressionRef.current);
        }
        return;
      }
      // The current expression has an invalid or ambiguous interpretation.
      // Block the submit; the explanation is already shown under the field.
      event.preventDefault();
      event.stopPropagation();
    };
    document.addEventListener('submit', handleSubmitCapture, true);
    return () => {
      document.removeEventListener('submit', handleSubmitCapture, true);
    };
  }, []);

  const updateExpression = (value: string) => {
    setExpression(value);
    setAssumptions([]);
    const nextValue = { ...formData, expression: value };
    onChange(
      nextValue,
      fieldPathId.path,
      errorSchema('Interpretation pending.'),
      fieldPathId.$id,
    );
    scheduleParse(value);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      parse(expression);
    }
  };

  const preview = renderPreview ? renderPreview(formData, assumptions) : null;
  const title = schema.title || label || 'Expression';

  return (
    <Stack spacing={1.5} ref={rootRef}>
      <TextField
        id={`${fieldPathId.$id}-expression`}
        label={title}
        // The expression is optional: existing records without one stay
        // submittable, and a DOM-required control here would silently block
        // native form submission while it is empty.
        disabled={disabled}
        slotProps={{ htmlInput: { readOnly: readonly } }}
        value={expression}
        onChange={(event) => updateExpression(event.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={() => {
          onBlur(fieldPathId.$id, expression);
          // Parse on blur only when the expression changed since the last
          // parse; an immediate re-parse here shifts the layout mid-click
          // and can swallow a submit that started on this blur.
          if (expression && expression !== lastParsedRef.current) {
            scheduleParse(expression);
          }
        }}
        onFocus={() => onFocus(fieldPathId.$id, expression)}
        error={Boolean(message)}
        helperText={message || examples}
        fullWidth
      />
      {loading && (
        <Box
          sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
          role="status"
        >
          <CircularProgress size={16} />
          <Typography variant="body2">Interpreting expression...</Typography>
        </Box>
      )}
      {preview && (
        <Typography variant="body2" aria-live="polite">
          {preview}
        </Typography>
      )}
      {renderExtra && (
        <Box>
          {renderExtra({
            value: formData,
            expression,
            disabled,
            readonly,
            $id: fieldPathId.$id,
            markValid: (nextValue, nextAssumptions = []) => {
              setAssumptions(nextAssumptions);
              setMessage(null);
              lastResultRef.current = {
                expression: expressionRef.current,
                status: 'valid',
              };
              onChange(
                nextValue,
                fieldPathId.path,
                {},
                fieldPathId.$id,
              );
            },
            showError: (errorMessage: string) =>
              emitError({ ...formData, expression }, errorMessage),
          })}
        </Box>
      )}
    </Stack>
  );
}
