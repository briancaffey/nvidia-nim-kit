<template>
  <div class="flex items-center justify-center">
    <NuxtImg
      :src="logoPath"
      :alt="alt"
      :class="imgClass"
      :width="width"
      :height="height"
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
  return colorMode.value === 'dark'
    ? '/img/nim_white.png'
    : '/img/nim_black.png'
})
</script>
