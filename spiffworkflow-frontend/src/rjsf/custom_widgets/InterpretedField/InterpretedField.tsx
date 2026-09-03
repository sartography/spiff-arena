import { FieldProps, getUiOptions } from '@rjsf/utils';
import { Form as MuiForm } from '@rjsf/mui';
// eslint-disable-next-line import-x/no-rename-default
import rjsfValidator from '@rjsf/validator-ajv8';
import {
  AutoAwesome,
  CheckCircleOutline,
  Close,
  Tune,
} from '@mui/icons-material';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  IconButton,
  InputAdornment,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { KeyboardEvent, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import HttpService from '../../../services/HttpService';

/**
 * A resolver-provided disambiguation pick. The frontend renders these
 * generically and sends the chosen value back through the resolver for
 * validation, so it never needs to understand what the value means.
 */
export type InterpretedChoice = {
  label: string;
  detail?: string;
  value: Record<string, unknown>;
  assumptions?: string[];
};

/**
 * Structured result returned by an expression resolver extension.
 * The resolver owns every word of user-facing text: the frontend only
 * renders preview/detail/assumptions/choices without interpreting them.
 */
export type InterpretedResult = {
  status: 'valid' | 'invalid' | 'ambiguous';
  value?: Record<string, unknown>;
  preview?: string;
  detail?: string;
  assumptions?: string[];
  choices?: InterpretedChoice[];
  edit_defaults?: Record<string, unknown>;
  errors?: { code: string; message: string }[];
};

// ui:options keys that configure the field itself instead of flowing through
// to the extension resolver as extension_input.
const RESERVED_OPTION_KEYS = [
  'resolver',
  'idleMilliseconds',
  'examples',
  'emptyMessage',
  'placeholder',
  'suggestions',
  'editSchema',
  'editUiSchema',
  'editButtonLabel',
  'valueDefaults',
  'revalidateEdits',
  'manualEditNote',
];

const BROWSER_TIME_ZONE_TOKEN = '$browserTimeZone';

const errorSchema = (message: string) => ({ __errors: [message] });

const hasStructuredData = (value: Record<string, unknown>) =>
  Object.entries(value).some(
    ([key, entryValue]) =>
      key !== 'expression' &&
      entryValue !== undefined &&
      entryValue !== null &&
      entryValue !== '',
  );

export default function InterpretedField({
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
}: FieldProps<Record<string, unknown>>) {
  const { t } = useTranslation();
  const options = getUiOptions(uiSchema || {});
  const resolver = String(options.resolver || '');
  const idleMilliseconds = Number(options.idleMilliseconds || 500);
  const browserTimeZone =
    Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
  const suggestions = Array.isArray(options.suggestions)
    ? options.suggestions.filter(
        (suggestion): suggestion is string => typeof suggestion === 'string',
      )
    : [];
  const editSchema = (
    typeof options.editSchema === 'object' && options.editSchema !== null
      ? options.editSchema
      : undefined
  ) as Record<string, unknown> | undefined;
  const editUiSchema = (
    typeof options.editUiSchema === 'object' && options.editUiSchema !== null
      ? options.editUiSchema
      : undefined
  ) as Record<string, unknown> | undefined;
  const editButtonLabel = String(
    options.editButtonLabel || t('interpreted_field_adjust_values'),
  );
  const revalidateEdits = options.revalidateEdits !== false;
  const manualEditNote = String(
    options.manualEditNote || t('interpreted_field_edited_manually'),
  );

  const [expression, setExpression] = useState(
    typeof formData.expression === 'string' ? formData.expression : '',
  );
  const [assumptions, setAssumptions] = useState<string[]>([]);
  const [preview, setPreview] = useState<string | null>(null);
  const [detail, setDetail] = useState<string | null>(null);
  const [choices, setChoices] = useState<InterpretedChoice[]>([]);
  const [editDefaults, setEditDefaults] = useState<
    Record<string, unknown> | undefined
  >(undefined);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editDraft, setEditDraft] = useState<Record<string, unknown>>({});
  const [editErrors, setEditErrors] = useState(false);
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
  // Mirror of the structured value for asynchronous callbacks: the parse
  // scheduled by the debounce timer closes over its render's formData,
  // which a freshly resolved result may already have replaced.
  const formDataRef = useRef(formData);
  formDataRef.current = formData;

  const emptyMessage = String(
    options.emptyMessage || t('interpreted_field_enter_expression'),
  );
  const examples = String(options.examples || '');
  const placeholder = String(options.placeholder || '');

  // Fill configured defaults for missing structured keys. The
  // '$browserTimeZone' token resolves to the browser IANA zone so
  // resolvers can seed zone-aware values without server knowledge.
  // Re-runs when form data arrives because task data can load after
  // the first render; the fill is idempotent so it never loops.
  useEffect(() => {
    const valueDefaults = options.valueDefaults;
    if (
      typeof valueDefaults !== 'object' ||
      valueDefaults === null ||
      Array.isArray(valueDefaults)
    ) {
      return;
    }
    const nextValue = { ...formData };
    let changed = false;
    for (const [key, defaultValue] of Object.entries(
      valueDefaults as Record<string, unknown>,
    )) {
      const current = nextValue[key];
      if (current === undefined || current === null || current === '') {
        const filled =
          defaultValue === BROWSER_TIME_ZONE_TOKEN
            ? browserTimeZone
            : defaultValue;
        // Only report an actual difference: filling an empty key with an
        // empty default must not emit a change on every render.
        if (filled !== current) {
          nextValue[key] = filled;
          changed = true;
        }
      }
    }
    if (changed) {
      onChange(nextValue, fieldPathId.path, undefined, fieldPathId.$id);
    }
  });

  useEffect(
    () => () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      requestRef.current?.controller.abort();
    },
    [],
  );

  const emitError = (
    nextValue: Record<string, unknown>,
    errorMessage: string,
  ) => {
    setMessage(errorMessage);
    onChange(
      nextValue,
      fieldPathId.path,
      errorSchema(errorMessage),
      fieldPathId.$id,
    );
  };

  const parse = (value: string, valueOverride?: Record<string, unknown>) => {
    lastParsedRef.current = value;
    if (!value.trim() && !valueOverride) {
      pendingParseRef.current = false;
      loadingRef.current = false;
      if (hasStructuredData(formDataRef.current)) {
        // The expression was cleared but structured data remains. That is the
        // same state an existing record opens in, so it must stay submittable.
        setAssumptions([]);
        setChoices([]);
        setMessage(null);
        lastResultRef.current = { expression: value, status: 'valid' };
        onChange(
          { ...formDataRef.current, expression: value },
          fieldPathId.path,
          {},
          fieldPathId.$id,
        );
        maybeSubmitAfterParse();
        return;
      }
      emitError({ ...formDataRef.current, expression: value }, emptyMessage);
      return;
    }
    if (!resolver.match(/^[a-zA-Z0-9][a-zA-Z0-9/_-]*$/)) {
      pendingParseRef.current = false;
      loadingRef.current = false;
      emitError(
        { ...formDataRef.current, expression: value },
        t('interpreted_field_invalid_resolver'),
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
    setChoices([]);

    const resolvedOptions = Intl.DateTimeFormat().resolvedOptions();
    const extensionInput: Record<string, unknown> = {};
    for (const [key, optionValue] of Object.entries(options)) {
      if (!RESERVED_OPTION_KEYS.includes(key)) {
        extensionInput[key] = optionValue;
      }
    }
    extensionInput.expression = value;
    // The edited value, or an empty object for a fresh expression parse.
    // Resolvers use its presence to tell validation apart from parsing.
    extensionInput.value = valueOverride ?? {};
    extensionInput.reference_instant = new Date().toISOString();
    extensionInput.time_zone = resolvedOptions.timeZone;
    extensionInput.locale = resolvedOptions.locale;
    HttpService.makeCallToBackend({
      path: `/v1.0/extensions/${resolver}`,
      httpMethod: 'POST',
      signal: controller.signal,
      postBody: { extension_input: extensionInput },
      successCallback: (response: {
        task_data?: { result?: InterpretedResult };
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
          setPreview(result.preview ?? null);
          setDetail(result.detail ?? null);
          setChoices([]);
          setEditDefaults(result.edit_defaults);
          setEditing(false);
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
        setChoices(
          Array.isArray(result?.choices) ? (result.choices ?? []) : [],
        );
        const resultMessage =
          result?.errors?.[0]?.message ||
          t('interpreted_field_could_not_interpret');
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
          t('interpreted_field_check_failed'),
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
    // Assumptions described the previous expression, but the preview and
    // detail still describe the last valid value, so they stay visible in
    // the neutral last-valid card until the new parse resolves.
    setAssumptions([]);
    const nextValue = { ...formDataRef.current, expression: value };
    // A new keystroke is not an error: reporting one would hoist an
    // "Errors" panel to the top of the form on every keystroke and shove
    // the input being typed into down the page. Submit gating observes the
    // parse refs directly, so it needs no error to do its job.
    onChange(nextValue, fieldPathId.path, undefined, fieldPathId.$id);
    scheduleParse(value);
  };

  const parseImmediately = (value: string) => {
    setExpression(value);
    setAssumptions([]);
    const nextValue = { ...formDataRef.current, expression: value };
    // See updateExpression: in-flight interpretation is not an error.
    onChange(nextValue, fieldPathId.path, undefined, fieldPathId.$id);
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    parse(value);
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

  const openEditor = () => {
    const seed = { ...(editDefaults ?? {}) };
    for (const [key, entryValue] of Object.entries(formData)) {
      if (key !== 'expression' && seed[key] === undefined) {
        seed[key] = entryValue;
      }
    }
    setEditDraft(seed);
    setEditErrors(false);
    setEditing(true);
  };

  const applyEdits = () => {
    if (editErrors) {
      return;
    }
    if (!revalidateEdits) {
      setAssumptions([manualEditNote]);
      setPreview(null);
      setDetail(null);
      setChoices([]);
      setEditing(false);
      lastResultRef.current = {
        expression: expressionRef.current,
        status: 'valid',
      };
      onChange(
        { ...editDraft, expression: expressionRef.current },
        fieldPathId.path,
        {},
        fieldPathId.$id,
      );
      return;
    }
    // The resolver re-validates the edited value and returns a fresh
    // preview, so the field never has to understand the value it holds.
    parse(expressionRef.current, editDraft);
  };

  const title = schema.title || label || 'Expression';
  const showValidCard =
    !message && (preview || detail || assumptions.length > 0);
  const showLastValidCard =
    Boolean(message) && (preview || detail) && hasStructuredData(formData);

  return (
    <Stack spacing={1.5} ref={rootRef}>
      <TextField
        id={`${fieldPathId.$id}-expression`}
        label={title}
        // The expression is optional: existing records without one stay
        // submittable, and a DOM-required control here would silently block
        // native form submission while it is empty.
        disabled={disabled}
        slotProps={{
          htmlInput: {
            readOnly: readonly,
            autoComplete: 'off',
            autoCapitalize: 'off',
            spellCheck: false,
            placeholder,
          },
          input: {
            startAdornment: (
              <InputAdornment position="start">
                <AutoAwesome fontSize="small" color="action" />
              </InputAdornment>
            ),
            endAdornment: expression ? (
              <InputAdornment position="end">
                <IconButton
                  aria-label={t('interpreted_field_clear_expression')}
                  size="small"
                  edge="end"
                  disabled={disabled || readonly}
                  onClick={() => updateExpression('')}
                >
                  <Close fontSize="small" />
                </IconButton>
              </InputAdornment>
            ) : undefined,
          },
        }}
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
      {suggestions.length > 0 && !disabled && !readonly && (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {suggestions.map((suggestion) => (
            <Chip
              key={suggestion}
              label={suggestion}
              size="small"
              variant="outlined"
              onClick={() => parseImmediately(suggestion)}
            />
          ))}
        </Box>
      )}
      {loading && (
        <Box
          sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
          role="status"
        >
          <CircularProgress size={16} />
          <Typography variant="body2">
            {t('interpreted_field_interpreting_expression')}
          </Typography>
        </Box>
      )}
      {showValidCard && (
        <Card
          variant="outlined"
          sx={{
            borderColor: 'success.main',
          }}
        >
          <CardContent sx={{ '&:last-child': { pb: 2 } }}>
            <Stack spacing={1}>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                <CheckCircleOutline color="success" fontSize="small" />
                <Stack spacing={0.5}>
                  {preview && (
                    <Typography
                      variant="body1"
                      fontWeight="medium"
                      aria-live="polite"
                    >
                      {preview}
                    </Typography>
                  )}
                  {detail && (
                    <Typography variant="body2" color="text.secondary">
                      {detail}
                    </Typography>
                  )}
                </Stack>
              </Box>
              {assumptions.length > 0 && (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {assumptions.map((assumption) => (
                    <Chip
                      key={assumption}
                      label={assumption}
                      size="small"
                      color="warning"
                      variant="filled"
                      title={t('interpreted_field_assumption_hint')}
                    />
                  ))}
                </Box>
              )}
              {editSchema && !disabled && !readonly && !editing && (
                <Box>
                  <Button
                    startIcon={<Tune />}
                    onClick={openEditor}
                    size="small"
                  >
                    {editButtonLabel}
                  </Button>
                </Box>
              )}
            </Stack>
          </CardContent>
        </Card>
      )}
      {showLastValidCard && (
        <Card variant="outlined">
          <CardContent sx={{ '&:last-child': { pb: 2 } }}>
            <Typography
              variant="caption"
              color="text.secondary"
              display="block"
              gutterBottom
            >
              {t('interpreted_field_last_valid_interpretation')}
            </Typography>
            {preview && <Typography variant="body2">{preview}</Typography>}
            {detail && (
              <Typography variant="body2" color="text.secondary">
                {detail}
              </Typography>
            )}
          </CardContent>
        </Card>
      )}
      {choices.length > 0 && (
        <Stack spacing={1}>
          <Typography variant="body2" fontWeight="medium">
            {t('interpreted_field_which_did_you_mean')}
          </Typography>
          {choices.map((choice, index) => (
            <Button
              key={`${choice.label}-${index}`}
              variant="outlined"
              onClick={() => parse(expressionRef.current, choice.value)}
              sx={{ justifyContent: 'flex-start', textAlign: 'left' }}
            >
              <Stack>
                <Typography variant="body2" fontWeight="medium">
                  {choice.label}
                </Typography>
                {choice.detail && (
                  <Typography variant="caption" color="text.secondary">
                    {choice.detail}
                  </Typography>
                )}
              </Stack>
            </Button>
          ))}
        </Stack>
      )}
      {editing && editSchema && (
        <Card variant="outlined">
          <CardContent>
            <Stack spacing={1.5}>
              <MuiForm
                schema={editSchema as any}
                uiSchema={{
                  'ui:submitButtonOptions': { norender: true },
                  ...(editUiSchema as object | undefined),
                }}
                formData={editDraft}
                validator={rjsfValidator}
                liveValidate
                showErrorList={false}
                noHtml5Validate
                onChange={(event: any) => {
                  setEditDraft(event.formData ?? {});
                  setEditErrors((event.errors ?? []).length > 0);
                }}
                onSubmit={(_data: any, event: any) => {
                  // The nested editor form must never navigate or submit
                  // the surrounding task form on Enter.
                  event.preventDefault();
                  event.stopPropagation();
                }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    gap: 1,
                    justifyContent: 'flex-end',
                    mt: 1,
                  }}
                >
                  <Button size="small" onClick={() => setEditing(false)}>
                    {t('cancel')}
                  </Button>
                  <Button
                    size="small"
                    variant="contained"
                    disabled={editErrors}
                    onClick={applyEdits}
                  >
                    {t('apply')}
                  </Button>
                </Box>
              </MuiForm>
            </Stack>
          </CardContent>
        </Card>
      )}
    </Stack>
  );
}
