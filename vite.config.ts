import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const isPlaygroundBuild = mode === 'playground'

  return {
    base: isPlaygroundBuild ? './' : '/',
    plugins: [vue()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    build: isPlaygroundBuild
      ? {
          outDir: 'playground-dist',
          sourcemap: true,
        }
      : {
          lib: {
            entry: fileURLToPath(new URL('./src/index.ts', import.meta.url)),
            name: 'ModelDesign',
            formats: ['es'],
            fileName: 'model-design',
            cssFileName: 'style',
          },
          sourcemap: true,
          emptyOutDir: true,
          rollupOptions: {
            external: ['vue'],
            output: {
              assetFileNames: (assetInfo) =>
                assetInfo.name === 'style.css'
                  ? 'style.css'
                  : 'assets/[name]-[hash][extname]',
            },
          },
        },
  }
})
