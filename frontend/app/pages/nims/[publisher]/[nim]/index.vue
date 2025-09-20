<template>
  <div class="container mx-auto px-4 py-8">
    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-16">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      <span class="ml-2 text-muted-foreground">Loading NIM details...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-16">
      <div class="text-destructive mb-4">
        <Icon name="lucide:alert-circle" class="h-12 w-12 mx-auto mb-4" />
        <h3 class="text-lg font-semibold mb-2">Failed to load NIM</h3>
        <p class="text-muted-foreground mb-4">{{ error }}</p>
        <Button @click="fetchNimDetails" variant="outline">
          <Icon name="lucide:refresh-cw" class="mr-2 h-4 w-4" />
          Try Again
        </Button>
      </div>
    </div>

    <!-- NIM Details -->
    <div v-else-if="nim" class="max-w-4xl mx-auto">
      <!-- Breadcrumb -->
      <nav class="mb-8">
        <ol class="flex items-center space-x-2 text-sm text-muted-foreground">
          <li>
            <NuxtLink to="/" class="hover:text-primary">Home</NuxtLink>
          </li>
          <li class="flex items-center">
            <Icon name="lucide:chevron-right" class="h-4 w-4 mx-2" />
            <NuxtLink to="/nims" class="hover:text-primary">NIMs</NuxtLink>
          </li>
          <li class="flex items-center">
            <Icon name="lucide:chevron-right" class="h-4 w-4 mx-2" />
            <span class="text-foreground">{{ publisher }}</span>
          </li>
          <li class="flex items-center">
            <Icon name="lucide:chevron-right" class="h-4 w-4 mx-2" />
            <span class="text-foreground">{{ modelName }}</span>
          </li>
        </ol>
      </nav>

      <!-- Header Section -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <!-- Image -->
        <div class="relative h-96 bg-gradient-to-br from-primary/20 to-primary/5 rounded-lg overflow-hidden">
          <NuxtImg
            :src="imageUrl"
            :alt="nim.id"
            class="w-full h-full object-cover"
            loading="eager"
          />
          <div class="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent" />
        </div>

        <!-- Details -->
        <div class="space-y-6">
          <!-- Publisher/Namespace -->
          <div class="text-sm text-muted-foreground">
            {{ publisher }}
          </div>

          <!-- Title -->
          <h1 class="text-3xl font-bold tracking-tight">
            {{ modelName }}
          </h1>

          <!-- Description -->
          <p class="text-lg text-muted-foreground leading-relaxed">
            {{ nim.description }}
          </p>

          <!-- Tags -->
          <div class="space-y-3">
            <h3 class="text-sm font-semibold text-foreground">Tags</h3>
            <div class="flex flex-wrap gap-2">
              <Badge
                v-for="tag in nim.tags"
                :key="tag"
                variant="secondary"
                class="text-sm"
              >
                {{ tag }}
              </Badge>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex flex-col sm:flex-row gap-3">
            <Button
              size="lg"
              class="flex-1"
              @click="openUrl(nim.url)"
            >
              <Icon name="lucide:external-link" class="mr-2 h-5 w-5" />
              View on NVIDIA Build
            </Button>
            <Button
              v-if="nim.invoke_url"
              size="lg"
              variant="outline"
              @click="copyInvokeUrl"
            >
              <Icon name="lucide:copy" class="mr-2 h-5 w-5" />
              Copy Invoke URL
            </Button>
          </div>
        </div>
      </div>

      <!-- Additional Details -->
      <Card class="p-6">
        <CardHeader>
          <CardTitle>Technical Details</CardTitle>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 class="text-sm font-semibold text-muted-foreground mb-1">Type</h4>
              <p class="text-sm">{{ nim.type }}</p>
            </div>
            <div v-if="nim.release_date">
              <h4 class="text-sm font-semibold text-muted-foreground mb-1">Release Date</h4>
              <p class="text-sm">{{ formatDate(nim.release_date) }}</p>
            </div>
            <div v-if="nim.model">
              <h4 class="text-sm font-semibold text-muted-foreground mb-1">Model</h4>
              <p class="text-sm font-mono">{{ nim.model }}</p>
            </div>
            <div v-if="nim.invoke_url">
              <h4 class="text-sm font-semibold text-muted-foreground mb-1">Invoke URL</h4>
              <p class="text-sm font-mono break-all">{{ nim.invoke_url }}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
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

const route = useRoute()
const config = useRuntimeConfig()
const nim = ref<NIM | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

// Extract publisher and model name from the route
const publisher = computed(() => route.params.publisher as string)
const modelName = computed(() => route.params.nim as string)
const nimId = computed(() => `${publisher.value}/${modelName.value}`)

// Construct image URL
const imageUrl = computed(() => {
  if (!nim.value) return ''
  return `${config.public.apiBase}/static/nims/${nim.value.img}`
})

const fetchNimDetails = async () => {
  try {
    loading.value = true
    error.value = null

    console.log('Fetching NIM details for:', nimId.value)
    const response = await $fetch<NIM>(`${config.public.apiBase}/api/nims/catalog/${encodeURIComponent(nimId.value)}`)
    console.log('Received NIM details:', response)
    nim.value = response
  } catch (err) {
    console.error('Failed to fetch NIM details:', err)
    error.value = err instanceof Error ? err.message : 'Failed to load NIM details'
  } finally {
    loading.value = false
  }
}

const openUrl = (url: string) => {
  window.open(url, '_blank', 'noopener,noreferrer')
}

const copyInvokeUrl = async () => {
  if (nim.value?.invoke_url) {
    try {
      await navigator.clipboard.writeText(nim.value.invoke_url)
      // You could add a toast notification here
      console.log('Invoke URL copied to clipboard')
    } catch (err) {
      console.error('Failed to copy invoke URL:', err)
    }
  }
}

const formatDate = (dateString: string) => {
  if (!dateString) return 'N/A'
  try {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  } catch {
    return dateString
  }
}

// Fetch NIM details on component mount
onMounted(() => {
  fetchNimDetails()
})

// Set page metadata
useHead({
  title: computed(() => nim.value ? `${nim.value.id} - NIM Kit` : 'NIM Details - NIM Kit'),
  meta: [
    { name: 'description', content: computed(() => nim.value?.description || 'NIM details page') }
  ]
})
</script>
