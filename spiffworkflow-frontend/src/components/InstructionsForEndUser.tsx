import React from 'react';
// @ts-ignore
import MDEditor from '@uiw/react-md-editor';

export default function InstructionsForEndUser({ task }: any) {
  if (!task) {
    return null;
  }
  let instructions =
    'There is no additional instructions or information for this task.';
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
