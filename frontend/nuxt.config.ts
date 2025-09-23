// https://nuxt.com/docs/api/configuration/nuxt-config
import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  ssr: true,
  components: [
    {
      path: '@/components/ui',
      prefix: 'Ui',
      extensions: ['.vue'], // <-- block .ts barrels from becoming components
    },
  ],
  css: ['~/assets/css/tailwind.css'],
  vite: {
    plugins: [
      tailwindcss(),
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
    '@nuxt/icon',
    '@nuxt/fonts',
    '@nuxt/eslint',
    ['@nuxtjs/color-mode', {
      classSuffix: ''
    }],
    'shadcn-nuxt',
    '@tresjs/nuxt'
  ],
  // @ts-ignore - shadcn-nuxt module configuration
  shadcn: {
    /**
     * Prefix for all the imported component
     */
    prefix: '',
    /**
     * Directory that the component lives in.
     * @default "./components/ui"
     */
    componentDir: './app/components/ui'
  }
})