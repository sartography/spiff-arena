/// <reference types="vite/client" />

// vite.config.ts runs vite-plugin-svgr over every *.svg (not just *.svg?react),
// with exportType: 'default', so a plain SVG import is a component, not a URL
// string -- override vite/client's default string typing to match.
declare module '*.svg' {
  import * as React from 'react';

  const ReactComponent: React.FunctionComponent<
    React.ComponentProps<'svg'> & {
      title?: string;
      titleId?: string;
      desc?: string;
      descId?: string;
    }
  >;

  export default ReactComponent;
}
