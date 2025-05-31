import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Εισάγουμε τους polyfill plugins για Esbuild
import { NodeGlobalsPolyfillPlugin } from '@esbuild-plugins/node-globals-polyfill';
import { NodeModulesPolyfillPlugin } from '@esbuild-plugins/node-modules-polyfill';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // Όταν συναντάται το import "buffer", πηγαίνουμε στο node_modules/buffer
      buffer: 'buffer',
    },
  },
  optimizeDeps: {
    esbuildOptions: {
      // Προσθέτουμε global = globalThis, και ένα dummy process.env για να μην σπάει
      define: {
        global: 'globalThis',
        'process.env': '{}',
      },
      // Προσθέτουμε τα Esbuild plugins για polyfilling
      plugins: [
        NodeGlobalsPolyfillPlugin({
          buffer: true,
          process: true,
        }),
        NodeModulesPolyfillPlugin()
      ],
    },
  },
  build: {
    rollupOptions: {
      // Αν χρησιμοποιείτε επιπλέον Node modules, εδώ μπορείτε να ορίσετε polyfills κι άλλα
    }
  },
});
