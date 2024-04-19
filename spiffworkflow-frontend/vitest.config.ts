import { defineConfig } from 'vite';

// https://vitejs.dev/config/
export default defineConfig({
  test: {
    include: ['./src/**/*.test.ts', './src/**/*.test.tsx'],
    setupFiles: ['test/vitest.setup.ts'],
    globals: true,
    environment: 'jsdom',
  },
});
