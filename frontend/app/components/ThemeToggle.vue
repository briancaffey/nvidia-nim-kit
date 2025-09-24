<template>
  <button
    @click="toggleTheme"
    class="inline-flex items-center justify-center w-9 h-9 rounded-md border border-input bg-background hover:bg-accent hover:text-accent-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
    style="cursor: pointer;"
  >
    <Icon
      :name="(colorMode?.value === 'dark') ? 'lucide:sun' : 'lucide:moon'"
      class="h-4 w-4 transition-transform duration-300 hover:scale-110"
      :class="(colorMode?.value === 'dark') ? 'rotate-180' : 'rotate-0'"
    />
  </button>
</template>

<script setup lang="ts">
// @ts-ignore - useColorMode is auto-imported by @nuxtjs/color-mode
const colorMode = useColorMode()

const toggleTheme = () => {
  if (colorMode && colorMode.preference !== undefined) {
    colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark'
  }
}
</script>
