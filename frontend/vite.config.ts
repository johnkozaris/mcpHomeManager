import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";
import { copyFileSync, readFileSync } from "fs";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const packageJson = JSON.parse(
  readFileSync(path.resolve(__dirname, "package.json"), "utf-8"),
) as { version: string };
const appVersion = process.env.APP_VERSION || packageJson.version;

/** Copy index.html → 404.html so Litestar's html_mode serves the SPA shell for unknown routes. */
function spaFallback(): Plugin {
  return {
    name: "spa-fallback",
    closeBundle() {
      const dist = path.resolve(__dirname, "dist");
      copyFileSync(path.join(dist, "index.html"), path.join(dist, "404.html"));
    },
  };
}

export default defineConfig({
  define: {
    __APP_VERSION__: JSON.stringify(appVersion),
  },
  plugins: [
    react({
      babel: {
        plugins: [["babel-plugin-react-compiler"]],
      },
    }),
    tailwindcss(),
    spaFallback(),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          "vendor-react": ["react", "react-dom", "@tanstack/react-router"],
          "vendor-query": ["@tanstack/react-query"],
          "vendor-recharts": ["recharts"],
        },
      },
    },
  },
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/mcp": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
