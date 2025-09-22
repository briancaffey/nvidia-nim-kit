<template>
  <div class="container mx-auto px-4 py-8">
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
        Inference Gallery
      </h1>
      <p class="text-gray-600 dark:text-gray-400">
        Browse and explore all inference requests from your NIMs
      </p>
    </div>

    <!-- Gallery Component -->
    <InferenceGallery />
  </div>
</template>

<script setup lang="ts">
import InferenceGallery from '~/components/InferenceGallery.vue'

// Set page metadata
useHead({
  title: 'Gallery - NVIDIA NIM Kit',
  meta: [
    { name: 'description', content: 'Browse and explore inference requests from your NIMs' }
  ]
})
</script>
