import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// SPA is served by FastAPI from frontend/dist in production. In dev, proxy the
// API to the local uvicorn server so cookies stay same-origin.
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8765",
        changeOrigin: true,
      },
    },
  },
});
