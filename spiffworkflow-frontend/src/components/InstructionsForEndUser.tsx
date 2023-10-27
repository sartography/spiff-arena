import React, { useEffect, useState } from 'react';
// @ts-ignore
import { Toggle } from '@carbon/react';
import FormattingService from '../services/FormattingService';
import MarkdownRenderer from './MarkdownRenderer';

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
  instructions = FormattingService.checkForSpiffFormats(instructions);

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

  let className = 'markdown';
  if (collapsed) {
    className += ' markdown-collapsed';
  }

  return (
    <div>
      <div className={className}>
        {/*
          https://www.npmjs.com/package/@uiw/react-md-editor switches to dark mode by default by respecting @media (prefers-color-scheme: dark)
          This makes it look like our site is broken, so until the rest of the site supports dark mode, turn off dark mode for this component.
        */}

        <MarkdownRenderer linkTarget="_blank" source={instructions} />
      </div>
      {showCollapseToggle()}
    </div>
  );
}
