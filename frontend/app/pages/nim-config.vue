<template>
  <div class="container mx-auto px-4 py-8 max-w-6xl">

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Configured NIMs List -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <Icon name="lucide:server" class="h-5 w-5" />
            Configured NIMs
          </CardTitle>
          <CardDescription>
            Currently configured NVIDIA Inference Microservices
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div v-if="configuredNims.length === 0" class="text-center py-8 text-muted-foreground">
            <Icon name="lucide:server-off" class="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No NIMs configured yet</p>
            <p class="text-sm">Add your first NIM configuration using the form on the right</p>
          </div>
          <div v-else class="space-y-3">
            <div
              v-for="nim in configuredNims"
              :key="nim.nim_id"
              class="p-4 border rounded-lg bg-card"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-2">
                    <Icon name="lucide:server" class="h-4 w-4 text-muted-foreground" />
                    <code class="text-sm font-mono font-medium">{{ nim.nim_id }}</code>
                  </div>
                  <div class="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span class="text-muted-foreground">Host:</span>
                      <span class="ml-1 font-mono">{{ nim.host }}</span>
                    </div>
                    <div>
                      <span class="text-muted-foreground">Port:</span>
                      <span class="ml-1 font-mono">{{ nim.port }}</span>
                    </div>
                    <div class="col-span-2">
                      <span class="text-muted-foreground">Type:</span>
                      <span class="ml-1">{{ getNimTypeLabel(nim.nim_type) }}</span>
                    </div>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  @click="deleteNim(nim.nim_id)"
                  :disabled="isDeleting"
                  class="text-destructive hover:text-destructive"
                >
                  <Icon name="lucide:trash-2" class="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
          <div class="mt-4">
            <Button variant="outline" @click="loadConfiguredNims" :disabled="isLoading">
              <Icon name="lucide:refresh-cw" class="mr-2 h-4 w-4" />
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>

      <!-- Add New NIM Form -->
      <NIMConfigForm
        @submit="handleFormSubmit"
        @success="handleFormSuccess"
        @error="handleFormError"
      />
    </div>

    <!-- Status Messages -->
    <div v-if="statusMessage" class="mt-6">
      <Alert :variant="statusType">
        <Icon :name="statusIcon" class="h-4 w-4" />
        <AlertTitle>{{ statusTitle }}</AlertTitle>
        <AlertDescription>{{ statusMessage }}</AlertDescription>
      </Alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import NIMConfigForm from '~/components/NIMConfigForm.vue'

// Types
interface NIMConfig {
  nim_id: string
  host: string
  port: number
  nim_type: string
  status: string
}

interface NIMFormData {
  nim_id: string
  host: string
  port: number
  nim_type: string
}

// Reactive state
const configuredNims = ref<NIMConfig[]>([])
const isLoading = ref(false)
const isDeleting = ref(false)

// Status messages
const statusMessage = ref('')
const statusType = ref<'default' | 'destructive'>('default')
const statusTitle = ref('')
const statusIcon = ref('')

// API configuration
const config = useRuntimeConfig()
const apiBase = config.public.apiBase

// API functions
const apiCall = async (url: string, options: RequestInit = {}) => {
  const response = await fetch(`${apiBase}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
  }

  return response.json()
}

const loadConfiguredNims = async () => {
  isLoading.value = true
  try {
    const response = await apiCall('/api/nims/')
    const nimIds = response.nim_ids || []

    // Load full configuration for each NIM
    const nims = []
    for (const nimId of nimIds) {
      try {
        const nimConfig = await apiCall(`/api/nims/${encodeURIComponent(nimId)}`)
        nims.push(nimConfig)
      } catch (error) {
        console.error(`Failed to load config for ${nimId}:`, error)
      }
    }

    configuredNims.value = nims
  } catch (error) {
    console.error('Failed to load configured NIMs:', error)
    configuredNims.value = []
  } finally {
    isLoading.value = false
  }
}

const handleFormSubmit = async (formData: NIMFormData) => {
  const nimId = formData.nim_id
  try {
    await apiCall(`/api/nims/${encodeURIComponent(nimId)}`, {
      method: 'POST',
      body: JSON.stringify({
        host: formData.host,
        port: formData.port,
        nim_type: formData.nim_type
      })
    })

    // Reload the list
    await loadConfiguredNims()

    showStatus('success', 'NIM Added', `Successfully added configuration for ${nimId}`)
  } catch (error) {
    showStatus('error', 'Add Failed', error instanceof Error ? error.message : 'Failed to add NIM configuration')
  }
}

const handleFormSuccess = (nimId: string) => {
  showStatus('success', 'NIM Added', `Successfully added configuration for ${nimId}`)
}

const handleFormError = (error: string) => {
  showStatus('error', 'Add Failed', error)
}

const deleteNim = async (nimId: string) => {
  if (!confirm(`Are you sure you want to delete the configuration for ${nimId}?`)) {
    return
  }

  isDeleting.value = true
  try {
    await apiCall(`/api/nims/${encodeURIComponent(nimId)}`, {
      method: 'DELETE'
    })

    // Reload the list
    await loadConfiguredNims()

    showStatus('success', 'NIM Deleted', `Successfully deleted configuration for ${nimId}`)
  } catch (error) {
    showStatus('error', 'Delete Failed', error instanceof Error ? error.message : 'Failed to delete NIM configuration')
  } finally {
    isDeleting.value = false
  }
}

const getNimTypeLabel = (nimType: string) => {
  const nimTypeOptions = [
    { value: 'llm', label: 'LLM (Large Language Model)' },
    { value: 'image_gen', label: 'Image Generation' },
    { value: '3d', label: '3D Generation' },
    { value: 'asr', label: 'Automatic Speech Recognition' },
    { value: 'tts', label: 'Text-to-Speech' },
    { value: 'studio_voice', label: 'Studio Voice' },
    { value: 'document', label: 'Document Processing' }
  ]
  const option = nimTypeOptions.find(opt => opt.value === nimType)
  return option ? option.label : nimType
}

const showStatus = (type: 'success' | 'error', title: string, message: string) => {
  statusType.value = type === 'error' ? 'destructive' : 'default'
  statusTitle.value = title
  statusMessage.value = message
  statusIcon.value = type === 'success' ? 'lucide:check-circle' : 'lucide:alert-circle'

  // Auto-hide success messages after 5 seconds
  if (type === 'success') {
    setTimeout(() => {
      statusMessage.value = ''
    }, 5000)
  }
}

// Lifecycle
onMounted(() => {
  loadConfiguredNims()
})

// Page metadata
useHead({
  title: 'NIM Configuration - NIM Kit',
  meta: [
    { name: 'description', content: 'Manage configuration settings for your NVIDIA Inference Microservices (NIMs)' }
  ]
})
</script>
