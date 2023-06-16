import React, { useEffect, useState } from 'react';
// @ts-ignore
import MDEditor from '@uiw/react-md-editor';
import { Toggle } from '@carbon/react';

type OwnProps = {
  task: any;
  defaultMessage?: string;
  allowCollapse?: boolean;
};

export default function InstructionsForEndUser({
  task,
  defaultMessage = '',
  allowCollapse = false,
}: OwnProps) {
  const [collapsed, setCollapsed] = useState<boolean>(false);
  const [collapsable, setCollapsable] = useState<boolean>(false);
  let instructions = defaultMessage;
  let { properties } = task;
  if (!properties) {
    properties = task.extensions;
  }
  const { instructionsForEndUser } = properties;
  if (instructionsForEndUser) {
    instructions = instructionsForEndUser;
  }

  const maxLineCount: number = 8;
  const maxWordCount: number = 75;

  const lineCount = (arg: string) => {
    return arg.split('\n').length;
  };

  const wordCount = (arg: string) => {
    return arg.split(' ').length;
  };

  useEffect(() => {
    if (
      allowCollapse &&
      (lineCount(instructions) >= maxLineCount ||
        wordCount(instructions) > maxWordCount)
    ) {
      setCollapsable(true);
      setCollapsed(true);
    } else {
      setCollapsable(false);
      setCollapsed(false);
    }
  }, [allowCollapse, instructions]);

  if (!task) {
    return null;
  }

  const toggleCollapse = () => {
    setCollapsed(!collapsed);
  };

  const showCollapseToggle = () => {
    if (collapsable) {
      return (
        <Toggle
          labelA="Show More"
          labelB="Show Less"
          onToggle={toggleCollapse}
          id="toggle-collapse"
        />
      );
    }
    return null;
  };

  let instructionsShown = instructions;
  if (collapsed) {
    if (wordCount(instructions) > maxWordCount) {
      instructionsShown = instructions
        .split(' ')
        .slice(0, maxWordCount)
        .join(' ');
      instructionsShown += '...';
    } else if (lineCount(instructions) > maxLineCount) {
      instructionsShown = instructions.split('\n').slice(0, 5).join(' ');
      instructionsShown += '...';
    }
  }

  return (
    <div style={{ margin: '20px 0 20px 0' }}>
      <div className="markdown">
        {/*
          https://www.npmjs.com/package/@uiw/react-md-editor switches to dark mode by default by respecting @media (prefers-color-scheme: dark)
          This makes it look like our site is broken, so until the rest of the site supports dark mode, turn off dark mode for this component.
        */}
        <div data-color-mode="light">
          <MDEditor.Markdown source={instructionsShown} />
        </div>
      </div>
      {showCollapseToggle()}
    </div>
  );
}
