import MDEditor from '@uiw/react-md-editor';
import { useTheme } from '@mui/material';
import FormattingService from '../services/FormattingService';

export default function MarkdownRenderer(props: any) {
  const isDark = useTheme().palette.mode === 'dark';
  const { source } = props;
  const newMarkdown = FormattingService.checkForSpiffFormats(source);
  let wrapperClassName = '';
  const propsToUse = props;
  if ('wrapperClassName' in propsToUse) {
    wrapperClassName = propsToUse.wrapperClassName;
    delete propsToUse.wrapperClassName;
  }
  return (
    <div
      data-color-mode={isDark ? 'dark' : 'light'}
      className={wrapperClassName}
    >
      {/* eslint-disable-next-line react/jsx-props-no-spreading */}
      <MDEditor.Markdown {...{ ...propsToUse, ...{ source: newMarkdown } }} />
    </div>
  );
}
