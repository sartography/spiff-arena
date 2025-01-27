import { useEffect, useState } from 'react';
import HttpService from '../services/HttpService';
// Import MUI components
import { Box, Typography } from '@mui/material';

// Define the props type
type OwnProps = {
  apiPath: string;
};

// Main component function
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
      <Box className="with-bottom-margin">
        {/* Use MUI Typography to render markdown content */}
        <Typography component="div">
          {/* Assuming MarkdownRenderer is a custom component, replace it with MUI's Box and Typography */}
          {markdownContents}
        </Typography>
      </Box>
    );
  }

  return null;
}
