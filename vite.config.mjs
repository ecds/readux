import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [vue(), react({ include: /\.(jsx|js)$/ })],

  resolve: {
    alias: {
      "@": path.resolve(__dirname, "apps/static/js"),
      "react-draggable": path.resolve(__dirname, "apps/static/js/react-draggable-stub.js"),
      // Full (runtime + compiler) build needed because the root Vue instance
      // mounts to a Django-rendered DOM template rather than an SFC template.
      vue: "vue/dist/vue.esm-bundler.js",
      // Use local ecds-annotator source directly to avoid double-bundling.
      "ecds-annotator": path.resolve(__dirname, "../ecds-annotator/src/index.jsx"),
    },
  },

  build: {
    // Write output alongside other static JS so Django's {% static %} tags
    // continue to work without any template changes.
    outDir: "apps/static/js",
    // Don't wipe the output directory — other static files live here.
    emptyOutDir: false,
    rollupOptions: {
      input: "./apps/static/js/index.js",
      output: {
        format: "iife",
        entryFileNames: "main.js",
        assetFileNames: "[name][extname]",
      },
    },
    sourcemap: true,
  },
});
