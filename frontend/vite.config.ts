import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

const DEFAULT_API_TARGET = "http://127.0.0.1:8000";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiTarget = (env.VITE_API_BASE_URL || DEFAULT_API_TARGET).replace(/\/$/, "");

  return {
    plugins: [react()],
    server: {
      port: Number(env.VITE_DEV_PORT) || 5173,
      proxy: {
        "/api": {
          target: apiTarget,
          changeOrigin: true,
        },
        "/health": {
          target: apiTarget,
          changeOrigin: true,
        },
      },
    },
    test: {
      environment: "jsdom",
      setupFiles: "./src/test/setup.ts",
      globals: true,
    },
  };
});
