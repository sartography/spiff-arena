import { useTheme } from '@mui/material';
import CodeMirror, { ReactCodeMirrorProps } from '@uiw/react-codemirror';

/**
 * A themed wrapper around CodeMirror that automatically applies the app's theme
 * and provides sensible defaults for common configurations.
 *
 * This component automatically:
 * - Applies dark/light theme based on the app's theme mode
 * - Sets reasonable default height and width
 *
 * All CodeMirror props can be overridden by passing them directly.
 *
 * @example
 * ```tsx
 * <ThemedCodeMirror
 *   value={jsonData}
 *   extensions={[json()]}
 *   onChange={(value) => setJsonData(value)}
 * />
 * ```
 */
export default function ThemedCodeMirror(props: ReactCodeMirrorProps) {
  const theme = useTheme();
  const codeMirrorTheme = theme.palette.mode === 'dark' ? 'dark' : 'light';

  // Merge defaults with provided props
  const defaultProps: Partial<ReactCodeMirrorProps> = {
    height: '600px',
    width: 'auto',
    theme: codeMirrorTheme,
  };

  return <CodeMirror {...defaultProps} {...props} />;
}
