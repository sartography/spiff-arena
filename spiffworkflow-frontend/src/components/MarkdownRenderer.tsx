import MDEditor from '@uiw/react-md-editor';

export default function MarkdownRenderer(props: any) {
  let wrapperClassName = '';
  const propsToUse = props;
  if ('wrapperClassName' in propsToUse) {
    wrapperClassName = propsToUse.wrapperClassName;
    delete propsToUse.wrapperClassName;
  }
  return (
    <div data-color-mode="light" className={wrapperClassName}>
      {/* eslint-disable-next-line react/jsx-props-no-spreading */}
      <MDEditor.Markdown {...propsToUse} />
    </div>
  );
}
