import { defineConfig } from 'vite';

// relative base so the built dist/ opens from any local static server, offline
export default defineConfig({
  base: './',
  // decisions go to `python -m f2f.serve` in dev too
  server: { port: 5173, strictPort: true, proxy: { '/api': 'http://127.0.0.1:8600' } },
});
