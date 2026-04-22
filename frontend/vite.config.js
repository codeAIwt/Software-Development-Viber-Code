import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": {
        target: "http://192.168.1.4:8000",
        changeOrigin: true,
      },
      "/ws": {
        target: "ws://192.168.1.4:8000",
        changeOrigin: true,
        ws: true,
      },
    },
  },
});
