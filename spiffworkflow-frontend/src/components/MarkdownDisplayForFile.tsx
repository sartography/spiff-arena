import MDEditor from '@uiw/react-md-editor';
import { useEffect, useState } from 'react';
import HttpService from '../services/HttpService';

type OwnProps = {
  apiPath: string;
};

export default function MarkdownDisplayForFile({ apiPath }: OwnProps) {
  const [markdownContents, setMarkdownContents] = useState<string | null>(null);

  useEffect(() => {
    const processResult = (result: any) => {
      if (result.file_contents) {
        setMarkdownContents(result.file_contents);
      }
    };

    HttpService.makeCallToBackend({
      path: apiPath,
      successCallback: processResult,
    });
  }, [apiPath]);

  if (markdownContents) {
    return (
      <div data-color-mode="light" className="with-bottom-margin">
        <MDEditor.Markdown linkTarget="_blank" source={markdownContents} />
      </div>
    );
  }

  return null;
}
