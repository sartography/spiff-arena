import preact from '@preact/preset-vite';
import { defineConfig } from 'vite';
import viteTsconfigPaths from 'vite-tsconfig-paths';
import svgr from 'vite-plugin-svgr';

const host = process.env.HOST ?? 'localhost';
const port = process.env.PORT ? parseInt(process.env.PORT, 10) : 7001;

export default defineConfig({
  // depending on your application, base can also be "/"
  base: '/',
  plugins: [
    // react(),
    // seems to replace preact. hot module replacement doesn't work, so commented out. also causes errors when navigating with TabList:
    // Cannot read properties of undefined (reading 'disabled')
    // prefresh(),
    // we need preact for bpmn-js-spiffworkflow. see https://forum.bpmn.io/t/custom-prop-for-service-tasks-typeerror-cannot-add-property-object-is-not-extensible/8487
    preact({ devToolsEnabled: false }),
    viteTsconfigPaths(),
    svgr({
      // svgr options: https://react-svgr.com/docs/options/
      svgrOptions: {
        exportType: 'default',
        ref: true,
        svgo: false,
        titleProp: true,
      },
      include: '**/*.svg',
    }),
  ],
  // for prefresh, from https://github.com/preactjs/prefresh/issues/454#issuecomment-1456491801, not working
  // optimizeDeps: {
  //   include: ['preact/hooks', 'preact/compat', 'preact']
  // },
  server: {
    // this ensures that the browser DOES NOT open upon server start
    open: false,
    host,
    port,
  },
  preview: {
    host,
    port,
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
  css: {
    preprocessorOptions: {
      scss: {
        // carbon creates these warnings
        silenceDeprecations: ['if-function'],
      },
    },
  },
});
