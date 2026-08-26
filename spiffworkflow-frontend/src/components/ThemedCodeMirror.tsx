import { useTheme } from '@mui/material';
import { useTranslation } from 'react-i18next';
import ReactCodeMirror, {
  EditorView,
  ReactCodeMirrorProps,
} from '@uiw/react-codemirror';

interface ThemedCodeMirrorProps extends ReactCodeMirrorProps {
  /**
   * Accessible name for the editor's contenteditable region (its role is
   * "textbox", so it needs one per WCAG 4.1.2). CodeMirror's content div is
   * generated internally, not a simple child we can put an aria-label on
   * directly -- it has to go through CodeMirror's own contentAttributes
   * extension instead. Defaults to a generic label so no usage ships
   * without one; pass something more specific (e.g. naming the file being
   * edited) where that context is available.
   */
  ariaLabel?: string;
}

/**
 * A themed wrapper around CodeMirror that automatically applies the app's theme
 * and provides sensible defaults for common configurations.
 *
 * This component automatically:
 * - Applies dark/light theme based on the app's theme mode
 * - Sets reasonable default height and width
 * - Gives the editor an accessible name
 *
 * All CodeMirror props can be overridden by passing them directly.
 *
 * @example
 * ```tsx
 * <ThemedCodeMirror
 *   value={jsonData}
 *   extensions={[json()]}
 *   onChange={(value) => setJsonData(value)}
 *   ariaLabel="JSON schema editor"
 * />
 * ```
 */
export default function ThemedCodeMirror({
  ariaLabel,
  extensions = [],
  ...props
}: ThemedCodeMirrorProps) {
  const theme = useTheme();
  const { t } = useTranslation();
  const codeMirrorTheme = theme.palette.mode === 'dark' ? 'dark' : 'light';

  // Merge defaults with provided props
  const defaultProps: Partial<ReactCodeMirrorProps> = {
    height: '600px',
    width: 'auto',
    theme: codeMirrorTheme,
  };

  const allExtensions = [
    ...extensions,
    EditorView.contentAttributes.of({
      'aria-label': ariaLabel || t('code_editor'),
    }),
  ];

  return (
    <ReactCodeMirror {...defaultProps} {...props} extensions={allExtensions} />
  );
}
