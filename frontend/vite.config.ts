import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { reportsPlugin } from "./reports-plugin";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), reportsPlugin(path.resolve(__dirname, "../reports"))],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // El backend usa el puerto 3100, igual que Compose.
      // Todas las llamadas HTTP del frontend pasan por aquí, nunca directo a MinIO/MariaDB.
      "/api": {
        target: "http://localhost:3100",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ""),
      },
    },
  },
});
