import { defineConfig } from 'vite';

// https://vitejs.dev/config/
export default defineConfig({
  test: {
    include: ['./src/**/*.test.ts', './src/**/*.test.tsx'],
    globals: true,
    environment: 'jsdom',
  },
});
