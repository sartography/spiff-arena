import preact from '@preact/preset-vite';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

import viteTsconfigPaths from 'vite-tsconfig-paths';

export default defineConfig({
  // depending on your application, base can also be "/"
  base: '/',
  // plugins: [react(), viteTsconfigPaths(), preact()],
  plugins: [
    // react(),
    preact({ prerender: { enabled: false } }),
    viteTsconfigPaths(),
  ],
  server: {
    // this ensures that the browser DOES NOT open upon server start
    open: false,
    port: 7001,
  },
  preview: {
    port: 7001,
  },
  // optimizeDeps: {
  //   includes: ['bpmn-js-spiffworkflow'],
  // },
  resolve: {
    alias: {
      // 'bpmn-js': `${process.env.HOME}/projects/github/sartography/spiff-arena/spiffworkflow-frontend/node_modules/bpmn-js`,
      inferno:
        process.env.NODE_ENV !== 'production'
          ? 'inferno/dist/index.dev.esm.js'
          : 'inferno/dist/index.esm.js',
    },
    preserveSymlinks: true,
  },
  // esbuild: {
  //   loader: 'tsx',
  // },
  // optimizeDeps: {
  //   esbuildOptions: {
  //     loader: {
  //       '.js': 'tsx',
  //     },
  //   },
  // },
});
