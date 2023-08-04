import Editor from '@monaco-editor/react';

export default function AuthenticationConfiguration() {
  return (
    <>
      <p>Local Configuration</p>
      <Editor
        height={600}
        width="auto"
        defaultLanguage="json"
        defaultValue=""
        onChange={(_) => null}
      />
    </>
  );
}
