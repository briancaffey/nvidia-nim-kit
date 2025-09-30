<template>
  <div class="relative w-full h-screen overflow-hidden">
    <!-- Image Container -->
    <div class="relative w-full h-full">
      <div
        v-for="(image, index) in images"
        :key="index"
        class="absolute inset-0 w-full h-full transition-opacity duration-1000 ease-in-out"
        :class="{ 'opacity-100': currentIndex === index, 'opacity-0': currentIndex !== index }"
      >
        <img
          :src="image.src"
          :alt="image.alt"
          class="w-full h-full object-cover"
        />
        <!-- Overlay for better text readability - more transparent -->
        <div class="absolute inset-0 bg-black/60 dark:bg-black/70"></div>
      </div>
    </div>

    <!-- Content Overlay -->
    <div class="absolute inset-0 flex items-center justify-center z-10">
      <div class="text-center text-white px-4 max-w-3xl mx-auto transform -translate-y-8">
        <div class="flex justify-center mb-4">
          <Logo width="60" height="80" />
        </div>
        <h1 class="text-4xl font-bold tracking-tight sm:text-6xl mb-6">
          Welcome to <span class="text-primary">NIM Kit</span>
        </h1>
        <p class="text-xl text-white/90 mb-8">
          A powerful toolkit for building AI applications with NVIDIA NIMs.
        </p>
        <div class="flex flex-col sm:flex-row gap-4 justify-center">
          <Button size="lg" class="text-lg px-8">
            Get Started
            <Icon name="lucide:arrow-right" class="ml-2 h-5 w-5" />
          </Button>
          <NuxtLink to="/about">
            <Button variant="outline" size="lg" class="text-lg px-8 bg-white/10 border-white/20 text-white hover:bg-white/20">
              Learn More
            </Button>
          </NuxtLink>
        </div>
      </div>
    </div>

    <!-- Navigation Dots -->
    <div class="absolute bottom-6 left-1/2 transform -translate-x-1/2 flex space-x-2 z-20">
      <button
        v-for="(image, index) in images"
        :key="index"
        @click="goToSlide(index)"
        class="w-3 h-3 rounded-full transition-all duration-300"
        :class="currentIndex === index
          ? 'bg-white scale-110'
          : 'bg-white/50 hover:bg-white/70'"
        :aria-label="`Go to slide ${index + 1}`"
      />
    </div>

    <!-- Navigation Arrows (Optional) -->
    <button
      @click="previousSlide"
      class="absolute left-4 top-1/2 transform -translate-y-1/2 z-20 p-2 rounded-full bg-black/20 hover:bg-black/40 transition-colors"
      aria-label="Previous slide"
    >
      <Icon name="lucide:chevron-left" class="h-6 w-6 text-white" />
    </button>
    <button
      @click="nextSlide"
      class="absolute right-4 top-1/2 transform -translate-y-1/2 z-20 p-2 rounded-full bg-black/20 hover:bg-black/40 transition-colors"
      aria-label="Next slide"
    >
      <Icon name="lucide:chevron-right" class="h-6 w-6 text-white" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

// Image data - easily extensible for future images
const images = ref([
  {
    src: '/img/jumbo/1.webp',
    alt: 'NIM Kit Technology Showcase 1'
  },
  {
    src: '/img/jumbo/2.webp',
    alt: 'NIM Kit Technology Showcase 2'
  },
  {
    src: '/img/jumbo/3.webp',
    alt: 'NIM Kit Technology Showcase 3'
  }
])

const currentIndex = ref(0)
let intervalId: NodeJS.Timeout | null = null

// Auto-advance slides every 4 seconds
const startAutoSlide = () => {
  intervalId = setInterval(() => {
    currentIndex.value = (currentIndex.value + 1) % images.value.length
  }, 4000)
}

const stopAutoSlide = () => {
  if (intervalId) {
    clearInterval(intervalId)
    intervalId = null
  }
}

// Navigation functions
const nextSlide = () => {
  currentIndex.value = (currentIndex.value + 1) % images.value.length
  restartAutoSlide()
}

const previousSlide = () => {
  currentIndex.value = currentIndex.value === 0
    ? images.value.length - 1
    : currentIndex.value - 1
  restartAutoSlide()
}

const goToSlide = (index: number) => {
  currentIndex.value = index
  restartAutoSlide()
}

const restartAutoSlide = () => {
  stopAutoSlide()
  startAutoSlide()
}

// Lifecycle hooks
onMounted(() => {
  startAutoSlide()
})

onUnmounted(() => {
  stopAutoSlide()
})

// Pause on hover (optional enhancement)
const pauseOnHover = () => {
  stopAutoSlide()
}

const resumeOnLeave = () => {
  startAutoSlide()
}
</script>
