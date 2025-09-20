<template>
  <div class="container mx-auto px-4 py-8">
    <!-- Header Section -->
    <section class="text-center py-8 mb-8">
      <div class="max-w-3xl mx-auto">
        <h1 class="text-4xl font-bold tracking-tight sm:text-5xl mb-4">
          NIM <span class="text-primary">Catalog</span>
        </h1>
        <p class="text-xl text-muted-foreground mb-6">
          Explore NVIDIA's collection of pre-trained models and AI capabilities
        </p>
      </div>
    </section>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-16">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      <span class="ml-2 text-muted-foreground">Loading NIMs...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-16">
      <div class="text-destructive mb-4">
        <Icon name="lucide:alert-circle" class="h-12 w-12 mx-auto mb-4" />
        <h3 class="text-lg font-semibold mb-2">Failed to load NIMs</h3>
        <p class="text-muted-foreground mb-4">{{ error }}</p>
        <Button @click="fetchNims" variant="outline">
          <Icon name="lucide:refresh-cw" class="mr-2 h-4 w-4" />
          Try Again
        </Button>
      </div>
    </div>

    <!-- NIMs Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <NIMCard
        v-for="nim in nims"
        :key="nim.id"
        :nim="nim"
      />
    </div>

    <!-- Empty State -->
    <div v-if="!loading && !error && nims.length === 0" class="text-center py-16">
      <Icon name="lucide:package" class="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
      <h3 class="text-lg font-semibold mb-2">No NIMs Found</h3>
      <p class="text-muted-foreground">No NIMs are currently available.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import NIMCard from '~/components/NIMCard.vue'

interface NIM {
  id: string
  url: string
  invoke_url?: string
  model?: string
  type: string
  tags: string[]
  description: string
  release_date?: string
  img: string
}

const config = useRuntimeConfig()
const nims = ref<NIM[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const fetchNims = async () => {
  try {
    loading.value = true
    error.value = null

    console.log('Fetching NIMs from:', `${config.public.apiBase}/api/nims/catalog`)
    const response = await $fetch<NIM[]>(`${config.public.apiBase}/api/nims/catalog`)
    console.log('Received NIMs:', response.length, 'items')
    nims.value = response
  } catch (err) {
    console.error('Failed to fetch NIMs:', err)
    error.value = err instanceof Error ? err.message : 'Failed to load NIMs'
  } finally {
    loading.value = false
  }
}

// Fetch NIMs on component mount
onMounted(() => {
  fetchNims()
})

// Set page metadata
useHead({
  title: 'NIMs Catalog - NIM Kit',
  meta: [
    { name: 'description', content: 'Explore NVIDIA\'s collection of pre-trained models and AI capabilities in the NIM Kit catalog.' }
  ]
})
</script>
