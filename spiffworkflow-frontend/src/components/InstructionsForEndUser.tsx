import React, { useEffect, useState } from 'react';
// @ts-ignore
import { Toggle } from '@carbon/react';
import FormattingService from '../services/FormattingService';
import MarkdownRenderer from './MarkdownRenderer';
import {
  BasicTask,
  ProcessInstanceTask,
  TaskInstructionForEndUser,
} from '../interfaces';

type OwnProps = {
  task?: BasicTask | ProcessInstanceTask | null;
  taskInstructionForEndUser?: TaskInstructionForEndUser;
  defaultMessage?: string;
  allowCollapse?: boolean;
  className?: string;
};

export default function InstructionsForEndUser({
  task,
  taskInstructionForEndUser,
  defaultMessage = '',
  allowCollapse = false,
  className,
}: OwnProps) {
  const [collapsed, setCollapsed] = useState<boolean>(false);
  const [collapsable, setCollapsable] = useState<boolean>(false);
  let instructions = defaultMessage;

  if (task) {
    let properties = null;
    if ('properties' in task) {
      properties = task.properties;
    }
    if (!properties && 'extensions' in task) {
      properties = task.extensions;
    }
    const { instructionsForEndUser } = properties;
    if (instructionsForEndUser) {
      instructions = instructionsForEndUser;
    }
  } else if (taskInstructionForEndUser) {
    instructions = taskInstructionForEndUser.instruction;
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

  // this is to allow toggling collapsed instructions
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

  let mdClassName = 'markdown';
  if (collapsed) {
    mdClassName += ' markdown-collapsed';
  }

  if (instructions) {
    return (
      <div className={className}>
        <div className={mdClassName}>
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

  return null;
}
