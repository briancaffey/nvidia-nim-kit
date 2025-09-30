<template>
  <div class="flex items-center justify-center">
    <NuxtImg
      :src="logoPath"
      :alt="alt"
      :class="imgClass"
      :width="width"
      :height="height"
      class="object-contain max-h-full"
      style="max-height: 100%;"
    />
  </div>
</template>

<script setup lang="ts">
interface Props {
  width?: number | string
  height?: number | string
  alt?: string
  imgClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  width: 32,
  height: 32,
  alt: 'NIM Kit Logo',
  imgClass: ''
})

// @ts-ignore - useColorMode is auto-imported by @nuxtjs/color-mode
const colorMode = useColorMode()

const logoPath = computed(() => {
  return '/img/nim_white.png'
})
</script>
