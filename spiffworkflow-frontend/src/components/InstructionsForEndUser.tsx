import React from 'react';
// @ts-ignore
import MDEditor from '@uiw/react-md-editor';

type OwnProps = {
  task: any;
  defaultMessage?: string;
};

export default function InstructionsForEndUser({
  task,
  defaultMessage = '',
}: OwnProps) {
  if (!task) {
    return null;
  }
  let instructions = defaultMessage;
  let { properties } = task;
  if (!properties) {
    properties = task.extensions;
  }
  const { instructionsForEndUser } = properties;
  if (instructionsForEndUser) {
    instructions = instructionsForEndUser;
  }
  return (
    <div className="markdown">
      {/*
        https://www.npmjs.com/package/@uiw/react-md-editor switches to dark mode by default by respecting @media (prefers-color-scheme: dark)
        This makes it look like our site is broken, so until the rest of the site supports dark mode, turn off dark mode for this component.
      */}
      <div data-color-mode="light">
        <MDEditor.Markdown source={instructions} />
      </div>
    </div>
  );
}
