const { defineConfig } = require('vite');

module.exports = defineConfig({
  cacheDir: 'node_modules/.vite',
  esbuild: {
    jsx: 'automatic',
  },
  optimizeDeps: {
    include: ['axios', 'react', 'react-dom', 'react/jsx-runtime', 'react-router-dom'],
  },
  plugins: [],
});
