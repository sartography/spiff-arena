import preact from '@preact/preset-vite';
import prefresh from '@prefresh/vite';

import { defineConfig } from 'vite';
// import react from '@vitejs/plugin-react';

import viteTsconfigPaths from 'vite-tsconfig-paths';

export default defineConfig({
  // depending on your application, base can also be "/"
  base: '/',
  plugins: [
    // react(),
    // seems to replace preact. hot module replacement doesn't work, so commented out. also causes errors when navigating with TabList:
    // Cannot read properties of undefined (reading 'disabled')
    // prefresh(),
    // we need preact for bpmn-js-spiffworkflow. see https://forum.bpmn.io/t/custom-prop-for-service-tasks-typeerror-cannot-add-property-object-is-not-extensible/8487
    preact(),
    viteTsconfigPaths(),
  ],
  // for prefresh, from https://github.com/preactjs/prefresh/issues/454#issuecomment-1456491801, not working
  // optimizeDeps: {
  //   include: ['preact/hooks', 'preact/compat', 'preact']
  // },
  server: {
    // this ensures that the browser DOES NOT open upon server start
    open: false,
    port: 7001,
  },
  preview: {
    port: 7001,
  },
  resolve: {
    alias: {
      inferno:
        process.env.NODE_ENV !== 'production'
          ? 'inferno/dist/index.dev.esm.js'
          : 'inferno/dist/index.esm.js',
    },
    preserveSymlinks: true,
  },
});
