import { useEffect, useState } from 'react';
import HttpService from '../services/HttpService';
import MarkdownRenderer from './MarkdownRenderer';

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
      <MarkdownRenderer
        linkTarget="_blank"
        source={markdownContents}
        wrapperClassName="with-bottom-margin"
      />
    );
  }

  return null;
}
