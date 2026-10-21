import { defineConfig } from 'vite';

// relative base so the built dist/ opens from any local static server, offline
export default defineConfig({ base: './', server: { port: 5173, strictPort: true } });
