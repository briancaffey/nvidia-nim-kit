<template>
  <div class="container mx-auto px-4 py-8 max-w-4xl">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold tracking-tight mb-2">NVIDIA API Configuration</h1>
      <p class="text-muted-foreground">
        Configure your NVIDIA API key for cloud inference services
      </p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Current API Key Status -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <Icon name="lucide:key" class="h-5 w-5" />
            Current API Key
          </CardTitle>
          <CardDescription>
            View the current NVIDIA API key status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div v-if="isLoading" class="text-center py-8">
            <Icon name="lucide:loader-2" class="h-8 w-8 mx-auto mb-4 animate-spin" />
            <p class="text-muted-foreground">Loading API key status...</p>
          </div>
          <div v-else-if="apiKeyStatus.has_key" class="space-y-4">
            <div class="p-4 border rounded-lg bg-card">
              <div class="flex items-center gap-2 mb-2">
                <Icon name="lucide:check-circle" class="h-4 w-4 text-green-500" />
                <span class="text-sm font-medium text-green-700 dark:text-green-400">API Key Configured</span>
              </div>
              <div class="space-y-2">
                <div>
                  <span class="text-sm text-muted-foreground">Preview:</span>
                  <code class="ml-2 text-sm font-mono bg-muted px-2 py-1 rounded">{{ apiKeyStatus.preview }}</code>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-sm text-muted-foreground">Source:</span>
                  <Badge :variant="apiKeyStatus.source === 'redis' ? 'default' : 'secondary'">
                    <Icon
                      :name="apiKeyStatus.source === 'redis' ? 'lucide:database' : 'lucide:settings'"
                      class="mr-1 h-3 w-3"
                    />
                    {{ apiKeyStatus.source === 'redis' ? 'Redis Storage' : 'Environment Variable' }}
                  </Badge>
                </div>
                <div class="text-sm text-muted-foreground">
                  <span v-if="apiKeyStatus.source === 'redis'">
                    This API key is stored securely in Redis and will be used for NVIDIA cloud inference services.
                  </span>
                  <span v-else>
                    This API key is provided via environment variable and will be used for NVIDIA cloud inference services.
                  </span>
                </div>
              </div>
            </div>
            <Button
              v-if="apiKeyStatus.source === 'redis'"
              variant="destructive"
              @click="deleteApiKey"
              :disabled="isDeleting"
              class="w-full"
            >
              <Icon name="lucide:trash-2" class="mr-2 h-4 w-4" />
              {{ isDeleting ? 'Deleting...' : 'Delete API Key' }}
            </Button>
            <div v-else class="p-3 border rounded-lg bg-muted/50">
              <div class="flex items-center gap-2 text-sm text-muted-foreground">
                <Icon name="lucide:info" class="h-4 w-4" />
                <span>API key from environment variable cannot be deleted from this interface.</span>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-8 text-muted-foreground">
            <Icon name="lucide:key-off" class="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No NVIDIA API key configured</p>
            <p class="text-sm">Add your API key using the form on the right</p>
          </div>
        </CardContent>
      </Card>

      <!-- Set API Key Form -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <Icon name="lucide:plus" class="h-5 w-5" />
            Set API Key
          </CardTitle>
          <CardDescription>
            Configure your NVIDIA API key for cloud inference
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div v-if="apiKeyStatus.has_key && apiKeyStatus.source === 'env'" class="p-4 border rounded-lg bg-muted/50 mb-4">
            <div class="flex items-center gap-2 text-sm text-muted-foreground">
              <Icon name="lucide:info" class="h-4 w-4" />
              <span>API key is already configured via environment variable. You can override it by setting a new key in Redis.</span>
            </div>
          </div>
          <form @submit.prevent="setApiKey" class="space-y-4">
            <div>
              <Label for="api-key">NVIDIA API Key</Label>
              <Input
                id="api-key"
                v-model="formData.api_key"
                type="password"
                placeholder="nvapi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                required
                class="mt-1"
              />
              <p class="text-sm text-muted-foreground mt-1">
                Your NVIDIA API key must start with "nvapi-"
              </p>
            </div>

            <Alert v-if="formData.api_key && !formData.api_key.startsWith('nvapi-')" variant="destructive">
              <Icon name="lucide:alert-circle" class="h-4 w-4" />
              <AlertTitle>Invalid API Key Format</AlertTitle>
              <AlertDescription>
                The API key must start with "nvapi-"
              </AlertDescription>
            </Alert>

            <Button
              type="submit"
              :disabled="isSaving || !isFormValid"
              class="w-full"
            >
              <Icon name="lucide:save" class="mr-2 h-4 w-4" />
              {{ isSaving ? 'Saving...' : (apiKeyStatus.has_key ? 'Override API Key' : 'Save API Key') }}
            </Button>
          </form>

          <div class="mt-6 p-4 border rounded-lg bg-muted/50">
            <h4 class="font-medium mb-2 flex items-center gap-2">
              <Icon name="lucide:info" class="h-4 w-4" />
              How to get your API key
            </h4>
            <ol class="text-sm text-muted-foreground space-y-1">
              <li>1. Visit <a href="https://build.nvidia.com" target="_blank" class="text-primary hover:underline">build.nvidia.com</a></li>
              <li>2. Sign up or log in to your account</li>
              <li>3. Navigate to your API keys section</li>
              <li>4. Create a new API key</li>
              <li>5. Copy the key (it will start with "nvapi-")</li>
            </ol>
          </div>
        </CardContent>
      </Card>
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
import { ref, computed, onMounted } from 'vue'

// Types
interface ApiKeyStatus {
  preview: string
  has_key: boolean
  source: string
  status: string
}

interface ApiKeyFormData {
  api_key: string
}

// Reactive state
const apiKeyStatus = ref<ApiKeyStatus>({
  preview: '',
  has_key: false,
  source: 'none',
  status: ''
})
const isLoading = ref(false)
const isSaving = ref(false)
const isDeleting = ref(false)

// Form data
const formData = ref<ApiKeyFormData>({
  api_key: ''
})

// Status messages
const statusMessage = ref('')
const statusType = ref<'default' | 'destructive'>('default')
const statusTitle = ref('')
const statusIcon = ref('')

// Computed properties
const isFormValid = computed(() => {
  return formData.value.api_key.trim() !== '' &&
         formData.value.api_key.startsWith('nvapi-')
})

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

const loadApiKeyStatus = async () => {
  isLoading.value = true
  try {
    const response = await apiCall('/api/nvidia/api-key')
    apiKeyStatus.value = response
  } catch (error) {
    console.error('Failed to load API key status:', error)
    showStatus('error', 'Load Failed', error instanceof Error ? error.message : 'Failed to load API key status')
  } finally {
    isLoading.value = false
  }
}

const setApiKey = async () => {
  if (!isFormValid.value) return

  isSaving.value = true
  try {
    await apiCall('/api/nvidia/api-key', {
      method: 'POST',
      body: JSON.stringify({
        api_key: formData.value.api_key
      })
    })

    // Reset form
    formData.value.api_key = ''

    // Reload the status
    await loadApiKeyStatus()

    showStatus('success', 'API Key Saved', 'NVIDIA API key has been saved successfully')
  } catch (error) {
    showStatus('error', 'Save Failed', error instanceof Error ? error.message : 'Failed to save API key')
  } finally {
    isSaving.value = false
  }
}

const deleteApiKey = async () => {
  isDeleting.value = true
  try {
    await apiCall('/api/nvidia/api-key', {
      method: 'DELETE'
    })

    // Reload the status
    await loadApiKeyStatus()

    showStatus('success', 'API Key Deleted', 'NVIDIA API key has been deleted successfully')
  } catch (error) {
    showStatus('error', 'Delete Failed', error instanceof Error ? error.message : 'Failed to delete API key')
  } finally {
    isDeleting.value = false
  }
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
  loadApiKeyStatus()
})

// Page metadata
useHead({
  title: 'NVIDIA API Configuration - NIM Kit',
  meta: [
    { name: 'description', content: 'Configure your NVIDIA API key for cloud inference services' }
  ]
})
</script>
