import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import viteTsconfigPaths from 'vite-tsconfig-paths';

export default defineConfig({
  // depending on your application, base can also be "/"
  base: '',
  plugins: [react(), viteTsconfigPaths()],
  server: {
    // this ensures that the browser DOES NOT open upon server start
    open: false,
    port: 7001,
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
