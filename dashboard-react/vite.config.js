import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Dev proxy: forward all /api requests to the running FastAPI backend
// so the React dev server works against it without CORS issues.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});
