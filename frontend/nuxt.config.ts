// https://nuxt.com/docs/api/configuration/nuxt-config
import tailwindcss from '@tailwindcss/vite'
import tsconfigPaths from 'vite-tsconfig-paths'

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  ssr: true,
  css: ['~/assets/css/tailwind.css'],
  vite: {
    plugins: [
      tailwindcss(),
      tsconfigPaths({
        ignoreConfigErrors: true,
      }),
    ],
  },
  devtools: { enabled: true },

  runtimeConfig: {
    public: {
      apiBase: 'http://localhost:8000',
    }
  },

  modules: [
    '@nuxt/image',
    '@nuxt/fonts',
    '@nuxt/eslint',
    ['@nuxtjs/color-mode', {
      classSuffix: ''
    }],
    '@tresjs/nuxt',
    ['@nuxt/icon', {
      collections: ['lucide']
    }],
    'shadcn-nuxt'
  ],
  // @ts-ignore - shadcn-nuxt module configuration
  shadcn: {
    /**
     * Prefix for all the imported component
     */
    prefix: 'Ui',
    /**
     * Directory that the component lives in.
     * @default "./components/ui"
     */
    componentDir: '~/components/ui'
  }
})