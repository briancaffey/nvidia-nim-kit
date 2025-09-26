<template>
  <div class="min-h-screen bg-muted/30 dark:bg-muted/20">
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
    <div v-else-if="nim">
      <!-- Banner Section -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6 rounded-lg border bg-background dark:bg-background border-border/50 dark:border-border/30 h-64 overflow-hidden">
        <!-- Text Content -->
        <div class="flex flex-col justify-center p-6">
          <!-- Publisher/Namespace -->
          <div class="text-sm text-muted-foreground mb-2">
            {{ provider }}
          </div>

          <!-- Title -->
          <h1 class="text-3xl font-bold tracking-tight mb-3">
            {{ name }}
          </h1>

          <!-- Description -->
          <p class="text-base text-muted-foreground mb-4 leading-relaxed">
            {{ nim.description }}
          </p>

          <!-- NIM Instance Badge -->
          <div v-if="nimConfig" class="mb-4">
            <Badge class="text-xs bg-muted text-muted-foreground border border-border">
              NIM Instance: {{ nimConfig.host }}:{{ nimConfig.port }}
            </Badge>
          </div>

          <!-- Tags -->
          <div class="flex flex-wrap gap-2">
            <Badge
              v-for="tag in nim.tags"
              :key="tag"
              class="text-sm bg-transparent text-teal-400 border border-teal-400 rounded-full hover:bg-teal-400/10 cursor-pointer"
            >
              {{ tag }}
            </Badge>
          </div>
        </div>

        <!-- Image Section -->
        <div class="relative h-full bg-gradient-to-br from-primary/20 to-primary/5 rounded-lg overflow-hidden">
          <NuxtImg
            :src="imageUrl"
            :alt="nim.id"
            class="w-full h-full object-cover object-center"
            loading="eager"
          />
          <!-- Fade effect on left side for dark/light mode -->
          <div class="absolute inset-0 bg-gradient-to-r from-background via-background/40 to-transparent" />
        </div>
      </div>

      <!-- Flux Generation Component -->
      <div v-if="isFluxModel">
        <FluxSchnellGeneration :nim-id="nimId" />
      </div>

      <!-- Trellis Generation Component -->
      <div v-else-if="isTrellisModel">
        <TrellisGeneration :nim-id="nimId" />
      </div>

      <!-- RIVA ASR Generation Component -->
      <div v-else-if="isAsrModel">
        <RivaAsrGeneration :nim-id="nimId" />
      </div>

      <!-- Studio Voice Generation Component -->
      <div v-else-if="isStudioVoiceModel">
        <StudioVoiceGeneration :nim-id="nimId" />
      </div>

      <!-- LLM Generation Component -->
      <div v-else-if="isLLMModel">
        <LLMGeneration :nim-id="nimId" />
      </div>

      <!-- NIM Configuration Form (when no config exists and not LLM) -->
      <div v-else-if="!nimConfig && !isConfiguring && !isLLMModel" class="mb-8">
        <NIMConfigForm
          :nim-id="nimId"
          :nim-id-disabled="true"
          title="Configure This NIM"
          description="This NIM is not yet configured. Please provide connection details to use it."
          submit-text="Configure NIM"
          @submit="handleConfigSubmit"
          @success="handleConfigSuccess"
          @error="handleConfigError"
        />
      </div>

      <!-- Success Message -->
      <div v-if="configSuccessMessage" class="mb-8">
        <Alert variant="default">
          <Icon name="lucide:check-circle" class="h-4 w-4" />
          <AlertTitle>NIM Configured Successfully!</AlertTitle>
          <AlertDescription>{{ configSuccessMessage }}</AlertDescription>
        </Alert>
      </div>

      <!-- Fallback Form for Unimplemented NIMs -->
      <div v-if="nimConfig && !isFluxModel && !isTrellisModel && !isAsrModel && !isStudioVoiceModel && !isLLMModel" class="mb-8">
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <Icon name="lucide:info" class="h-5 w-5" />
              NIM Interface Not Yet Implemented
            </CardTitle>
            <CardDescription>
              This NIM is configured but doesn't have a custom interface yet. You can still use it via API calls.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div class="space-y-4">
              <div class="p-4 bg-muted rounded-lg">
                <h4 class="font-medium mb-2">Connection Details:</h4>
                <div class="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span class="text-muted-foreground">Host:</span>
                    <span class="ml-1 font-mono">{{ nimConfig.host }}</span>
                  </div>
                  <div>
                    <span class="text-muted-foreground">Port:</span>
                    <span class="ml-1 font-mono">{{ nimConfig.port }}</span>
                  </div>
                </div>
              </div>
              <p class="text-sm text-muted-foreground">
                This NIM is ready to use! You can make API calls to <code class="bg-muted px-1 rounded">{{ nimConfig.host }}:{{ nimConfig.port }}</code>
                or use it programmatically in your applications.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import FluxSchnellGeneration from '~/components/FluxSchnellGeneration.vue'
import TrellisGeneration from '~/components/TrellisGeneration.vue'
import RivaAsrGeneration from '~/components/RivaAsrGeneration.vue'
import StudioVoiceGeneration from '~/components/StudioVoiceGeneration.vue'
import LLMGeneration from '~/components/LLMGeneration.vue'
import NIMConfigForm from '~/components/NIMConfigForm.vue'

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
const nimConfig = ref<{host: string, port: number, nim_type?: string} | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const isConfiguring = ref(false)
const configSuccessMessage = ref('')

// Extract provider and name from the route
const provider = computed(() => route.params.provider as string)
const name = computed(() => route.params.name as string)
const nimId = computed(() => `${provider.value}/${name.value}`)

// Construct image URL
const imageUrl = computed(() => {
  if (!nim.value) return ''
  return `${config.public.apiBase}/static/nims/${nim.value.img}`
})

// Check if this is a Flux model
const isFluxModel = computed(() => {
  return nimId.value === 'black-forest-labs/flux_1-schnell' ||
         nimId.value === 'black-forest-labs/flux_1-dev' ||
         nimId.value === 'black-forest-labs/flux_1-kontext-dev'
})

// Check if this is a Trellis model
const isTrellisModel = computed(() => {
  return nimId.value === 'microsoft/trellis'
})

// Check if this is an ASR model
const isAsrModel = computed(() => {
  return nimId.value === 'nvidia/parakeet-ctc-0_6b-asr'
})

// Check if this is a Studio Voice model
const isStudioVoiceModel = computed(() => {
  return nimId.value === 'nvidia/studiovoice'
})

// Check if this is an LLM model
const isLLMModel = computed(() => {
  // Check from catalog data first (nim.type), then from config (nimConfig.nim_type)
  return nim.value?.type === 'llm' || (nimConfig.value && nimConfig.value.nim_type === 'llm')
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

const fetchNimConfig = async () => {
  try {
    console.log('Fetching NIM config for:', nimId.value)
    const response = await $fetch<{host: string, port: number}>(`${config.public.apiBase}/api/nims/config/${encodeURIComponent(nimId.value)}`)
    console.log('Received NIM config:', response)
    nimConfig.value = response
  } catch (err) {
    console.error('Failed to fetch NIM config:', err)
    // Don't set error here as this is optional information
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

// Configuration handlers
const handleConfigSubmit = async (formData: {nim_id: string, host: string, port: number, nim_type: string}) => {
  isConfiguring.value = true
  try {
    await $fetch(`${config.public.apiBase}/api/nims/${encodeURIComponent(formData.nim_id)}`, {
      method: 'POST',
      body: {
        host: formData.host,
        port: formData.port,
        nim_type: formData.nim_type
      }
    })

    // Reload the config
    await fetchNimConfig()

    // Show success message
    configSuccessMessage.value = `Successfully configured ${formData.nim_id} at ${formData.host}:${formData.port}`

    // Hide success message after 5 seconds
    setTimeout(() => {
      configSuccessMessage.value = ''
    }, 5000)
  } catch (err) {
    console.error('Failed to configure NIM:', err)
    // Error handling is done by the form component
  } finally {
    isConfiguring.value = false
  }
}

const handleConfigSuccess = (nimId: string) => {
  configSuccessMessage.value = `Successfully configured ${nimId}`
  setTimeout(() => {
    configSuccessMessage.value = ''
  }, 5000)
}

const handleConfigError = (error: string) => {
  console.error('Configuration error:', error)
}

// Fetch NIM details on component mount
onMounted(() => {
  fetchNimDetails()
  fetchNimConfig()
})

// Set page metadata
useHead({
  title: computed(() => nim.value ? `${nim.value.id} - NIM Kit` : 'NIM Details - NIM Kit'),
  meta: [
    { name: 'description', content: computed(() => nim.value?.description || 'NIM details page') }
  ]
})
</script>