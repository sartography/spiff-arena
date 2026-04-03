import { useTheme } from '@mui/material';
import CodeMirrorMerge from 'react-codemirror-merge';
import { ReactCodeMirrorMergeProps } from 'react-codemirror-merge';

/**
 * A themed wrapper around CodeMirrorMerge that automatically applies the app's theme.
 *
 * This component automatically applies dark/light theme based on the app's theme mode.
 *
 * @example
 * ```tsx
 * <ThemedCodeMirrorMerge>
 *   <ThemedCodeMirrorMerge.Original
 *     value={originalJson}
 *     extensions={[json()]}
 *   />
 *   <ThemedCodeMirrorMerge.Modified
 *     value={modifiedJson}
 *     extensions={[json()]}
 *   />
 * </ThemedCodeMirrorMerge>
 * ```
 */
export default function ThemedCodeMirrorMerge(props: ReactCodeMirrorMergeProps) {
  const theme = useTheme();
  const codeMirrorTheme = theme.palette.mode === 'dark' ? 'dark' : 'light';

  return <CodeMirrorMerge theme={codeMirrorTheme} {...props} />;
}

// Re-export the Original and Modified components for convenience
ThemedCodeMirrorMerge.Original = CodeMirrorMerge.Original;
ThemedCodeMirrorMerge.Modified = CodeMirrorMerge.Modified;
