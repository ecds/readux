import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],

  resolve: {
    alias: {
      "@": path.resolve(__dirname, "apps/static/js"),
      // Full (runtime + compiler) build needed because the root Vue instance
      // mounts to a Django-rendered DOM template rather than an SFC template.
      vue: "vue/dist/vue.esm-bundler.js",
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
        entryFileNames: "main.js",
        // Keep chunk names stable so cached builds stay valid.
        chunkFileNames: "[name]-[hash].js",
        assetFileNames: "[name][extname]",
      },
    },
    sourcemap: true,
  },
  optimizeDeps: {
    exclude: ["ecds-annotator"],
  },
});
