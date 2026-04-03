import { useTheme } from '@mui/material';
import CodeMirrorMerge from 'react-codemirror-merge';
import type { CodeMirrorMergeProps } from 'react-codemirror-merge';

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
function ThemedCodeMirrorMergeBase(props: CodeMirrorMergeProps) {
  const theme = useTheme();
  const codeMirrorTheme = theme.palette.mode === 'dark' ? 'dark' : 'light';

  return <CodeMirrorMerge theme={codeMirrorTheme} {...props} />;
}

// Create a properly typed component with statics
type ThemedCodeMirrorMergeComponent = typeof ThemedCodeMirrorMergeBase & {
  Original: typeof CodeMirrorMerge.Original;
  Modified: typeof CodeMirrorMerge.Modified;
};

const ThemedCodeMirrorMerge = Object.assign(ThemedCodeMirrorMergeBase, {
  Original: CodeMirrorMerge.Original,
  Modified: CodeMirrorMerge.Modified,
}) as ThemedCodeMirrorMergeComponent;

export default ThemedCodeMirrorMerge;
