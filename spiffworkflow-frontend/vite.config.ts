import preact from '@preact/preset-vite';
import { defineConfig, loadEnv } from 'vite';
import svgr from 'vite-plugin-svgr';

const host = process.env.HOST ?? 'localhost';
const port = process.env.PORT ? parseInt(process.env.PORT, 10) : 7001;

export function resolveBasePath(env: Record<string, string | undefined>): string {
  // Build-time setting. Not a runtime SPIFFWORKFLOW_FRONTEND_RUNTIME_CONFIG_* var
  // because `base` is baked into asset URLs at `vite build` time.
  // Vite-agnostic name so it survives a bundler switch; existing build-time
  // VITE_* vars (VITE_VERSION_INFO etc.) are vite-specific client exposures
  // via import.meta.env and would need a compat layer if we switch.
  const raw = env.SPIFFWORKFLOW_FRONTEND_BUILD_TIME_BASE_PATH ?? '/';
  let base = raw.trim();
  if (!base) base = '/';
  if (!base.startsWith('/')) base = `/${base}`;
  if (!base.endsWith('/')) base += '/';
  return base;
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  // Allow both Vite-loaded env and direct process.env (for CI shell vars).
  const mergedEnv: Record<string, string | undefined> = { ...env, ...process.env };
  return {
  base: resolveBasePath(mergedEnv),
  plugins: [
    // react(),
    // seems to replace preact. hot module replacement doesn't work, so commented out. also causes errors when navigating with TabList:
    // Cannot read properties of undefined (reading 'disabled')
    // prefresh(),
    // we need preact for bpmn-js-spiffworkflow. see https://forum.bpmn.io/t/custom-prop-for-service-tasks-typeerror-cannot-add-property-object-is-not-extensible/8487
    preact({ devToolsEnabled: false }),
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
    // Deduplicate @bpmn-io/properties-panel so both the frontend and the symlinked
    // bpmn-js-spiffworkflow use the same instance (and thus the same bundled preact).
    dedupe: ['@bpmn-io/properties-panel', 'bpmn-js-properties-panel'],
    preserveSymlinks: true,
    tsconfigPaths: true,
  },
  };
});
