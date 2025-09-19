<template>
  <div class="container mx-auto px-4 py-8 max-w-6xl">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
        LLM Inference Requests
      </h1>
      <p class="text-gray-600 dark:text-gray-400">
        View and manage your LLM inference requests
      </p>
    </div>

    <!-- Action Buttons -->
    <div class="mb-8 flex space-x-4">
      <NuxtLink to="/llm/chat" class="inline-flex items-center space-x-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors cursor-pointer">
        <Icon name="lucide:message-square-plus" class="h-4 w-4" />
        <span>New Chat</span>
      </NuxtLink>
      <NuxtLink to="/llm/completion" class="inline-flex items-center space-x-2 px-4 py-2 border border-input bg-background hover:bg-accent hover:text-accent-foreground rounded-md transition-colors cursor-pointer">
        <Icon name="lucide:pen-tool" class="h-4 w-4" />
        <span>New Completion</span>
      </NuxtLink>
      <NuxtLink to="/llm/metrics" class="inline-flex items-center space-x-2 px-4 py-2 border border-input bg-background hover:bg-accent hover:text-accent-foreground rounded-md transition-colors cursor-pointer">
        <Icon name="lucide:bar-chart-3" class="h-4 w-4" />
        <span>Metrics Dashboard</span>
      </NuxtLink>
    </div>

    <!-- Success Alert -->
    <Alert v-if="successMessage" variant="default" class="mb-6 border-green-200 bg-green-50 text-green-800 dark:border-green-800 dark:bg-green-900/20 dark:text-green-200">
      <AlertTitle>Success</AlertTitle>
      <AlertDescription>{{ successMessage }}</AlertDescription>
    </Alert>

    <!-- Error Alert -->
    <Alert v-if="error" variant="destructive" class="mb-6">
      <AlertTitle>Error</AlertTitle>
      <AlertDescription>{{ error }}</AlertDescription>
    </Alert>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="flex items-center space-x-2">
        <Icon name="lucide:loader-2" class="h-4 w-4 animate-spin" />
        <span>Loading inference requests...</span>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!requests.length" class="text-center py-12">
      <Icon name="lucide:inbox" class="h-12 w-12 mx-auto text-gray-400 mb-4" />
      <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
        No LLM inference requests found
      </h3>
      <p class="text-gray-600 dark:text-gray-400 mb-4">
        Start by creating a new chat or completion request
      </p>
      <div class="flex justify-center space-x-4">
        <NuxtLink to="/llm/chat" class="inline-flex items-center space-x-2 px-3 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors cursor-pointer text-sm">
          <Icon name="lucide:message-square-plus" class="h-4 w-4" />
          <span>New Chat</span>
        </NuxtLink>
        <NuxtLink to="/llm/completion" class="inline-flex items-center space-x-2 px-3 py-2 border border-input bg-background hover:bg-accent hover:text-accent-foreground rounded-md transition-colors cursor-pointer text-sm">
          <Icon name="lucide:pen-tool" class="h-4 w-4" />
          <span>New Completion</span>
        </NuxtLink>
        <NuxtLink to="/llm/metrics" class="inline-flex items-center space-x-2 px-3 py-2 border border-input bg-background hover:bg-accent hover:text-accent-foreground rounded-md transition-colors cursor-pointer text-sm">
          <Icon name="lucide:bar-chart-3" class="h-4 w-4" />
          <span>View Metrics</span>
        </NuxtLink>
      </div>
    </div>

    <!-- Requests Grid -->
    <div v-else class="space-y-6">
      <!-- Stats -->
      <div class="flex space-x-3 mb-6">
        <div class="flex items-center space-x-2 px-3 py-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <Icon name="lucide:activity" class="h-4 w-4 text-blue-500" />
          <span class="text-sm font-medium text-blue-700 dark:text-blue-300">Total</span>
          <span class="text-sm font-bold text-blue-900 dark:text-blue-100">{{ stats.total }}</span>
        </div>

        <div class="flex items-center space-x-2 px-3 py-2 bg-green-50 dark:bg-green-900/20 rounded-lg">
          <Icon name="lucide:check-circle" class="h-4 w-4 text-green-500" />
          <span class="text-sm font-medium text-green-700 dark:text-green-300">Completed</span>
          <span class="text-sm font-bold text-green-900 dark:text-green-100">{{ stats.completed }}</span>
        </div>

        <div class="flex items-center space-x-2 px-3 py-2 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
          <Icon name="lucide:clock" class="h-4 w-4 text-yellow-500" />
          <span class="text-sm font-medium text-yellow-700 dark:text-yellow-300">Pending</span>
          <span class="text-sm font-bold text-yellow-900 dark:text-yellow-100">{{ stats.pending }}</span>
        </div>

        <div class="flex items-center space-x-2 px-3 py-2 bg-red-50 dark:bg-red-900/20 rounded-lg">
          <Icon name="lucide:x-circle" class="h-4 w-4 text-red-500" />
          <span class="text-sm font-medium text-red-700 dark:text-red-300">Errors</span>
          <span class="text-sm font-bold text-red-900 dark:text-red-100">{{ stats.errors }}</span>
        </div>
      </div>

      <!-- Filters -->
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div class="flex flex-wrap gap-4">
            <div class="flex items-center space-x-2">
              <Label for="status-filter">Status:</Label>
              <Select v-model="filters.status" @update:model-value="loadRequests">
                <SelectTrigger class="w-32">
                  <SelectValue placeholder="All" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="error">Error</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div class="flex items-center space-x-2">
              <Label for="type-filter">Type:</Label>
              <Select v-model="filters.requestType" @update:model-value="loadRequests">
                <SelectTrigger class="w-32">
                  <SelectValue placeholder="All" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="chat">Chat</SelectItem>
                  <SelectItem value="completion">Completion</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div class="flex items-center space-x-2">
              <Label for="nim-filter">NIM:</Label>
              <Select v-model="filters.nimId" @update:model-value="loadRequests">
                <SelectTrigger class="w-48">
                  <SelectValue placeholder="All NIMs" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All NIMs</SelectItem>
                  <SelectItem v-for="nim in availableNims" :key="nim.id" :value="nim.id">
                    {{ nim.id }}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button variant="outline" @click="clearFilters" class="ml-auto">
              <Icon name="lucide:x" class="h-4 w-4 mr-2" />
              Clear Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      <!-- Requests List -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <LLMInferenceRequestCard
          v-for="request in requests"
          :key="request.id"
          :request="request"
          @click="handleRequestClick"
          @delete="handleRequestDelete"
        />
      </div>

      <!-- Load More Button -->
      <div v-if="hasMore" class="text-center py-4">
        <Button @click="loadMore" :disabled="loading">
          <Icon name="lucide:loader-2" v-if="loading" class="h-4 w-4 mr-2 animate-spin" />
          <Icon name="lucide:plus" v-else class="h-4 w-4 mr-2" />
          Load More
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import LLMInferenceRequestCard from '@/components/LLMInferenceRequestCard.vue'

// Runtime config
const runtimeConfig = useRuntimeConfig()
const apiBase = runtimeConfig.public.apiBase

interface InferenceRequest {
  id: string
  request_type: string
  nim_id: string
  model: string
  stream: boolean
  status: string
  date_created: string
  date_updated: string
  input?: any
  output?: any
  error?: any
}

interface NIM {
  id: string
  name: string
}

const router = useRouter()

// Reactive state
const requests = ref<InferenceRequest[]>([])
const availableNims = ref<NIM[]>([])
const loading = ref(false)
const error = ref('')
const successMessage = ref('')
const hasMore = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)

const filters = ref({
  status: 'all',
  requestType: 'all',
  nimId: 'all'
})

// Computed properties
const stats = computed(() => {
  const total = requests.value.length
  const completed = requests.value.filter(r => r.status === 'completed').length
  const pending = requests.value.filter(r => r.status === 'pending').length
  const errors = requests.value.filter(r => r.status === 'error').length

  return { total, completed, pending, errors }
})

// Methods
const loadRequests = async (reset = true) => {
  if (loading.value) return

  loading.value = true
  error.value = ''

  try {
    const params = new URLSearchParams({
      type: 'LLM',
      limit: pageSize.value.toString()
    })

    if (filters.value.status && filters.value.status !== 'all') {
      params.append('status', filters.value.status)
    }
    if (filters.value.requestType && filters.value.requestType !== 'all') {
      params.append('request_type', filters.value.requestType)
    }
    if (filters.value.nimId && filters.value.nimId !== 'all') {
      params.append('nim_id', filters.value.nimId)
    }

    const response = await fetch(`${apiBase}/api/llm/requests?${params}`)
    if (!response.ok) {
      throw new Error(`Failed to load requests: ${response.statusText}`)
    }

    const data = await response.json()

    // Debug: Log the received data
    console.log('Received API data:', data)
    if (data.requests && data.requests.length > 0) {
      console.log('First request sample:', data.requests[0])
    }

    if (reset) {
      requests.value = data.requests || []
      currentPage.value = 1
    } else {
      requests.value.push(...(data.requests || []))
      currentPage.value++
    }

    hasMore.value = (data.requests || []).length === pageSize.value

    // Load detailed request data
    // await loadDetailedRequests()

  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load requests'
  } finally {
    loading.value = false
  }
}

const loadDetailedRequests = async () => {
  // Load detailed data for each request
  const promises = requests.value.map(async (request) => {
    try {
      const response = await fetch(`${apiBase}/api/llm/inference/${request.id}`)
      if (response.ok) {
        const detailedRequest = await response.json()
        return { ...request, ...detailedRequest }
      }
    } catch (err) {
      console.warn(`Failed to load details for request ${request.id}:`, err)
    }
    return request
  })

  const detailedRequests = await Promise.all(promises)
  requests.value = detailedRequests
}

const loadNims = async () => {
  try {
    const response = await fetch(`${apiBase}/api/nims/`)
    if (response.ok) {
      const data = await response.json()
      availableNims.value = data.nims || []
    }
  } catch (err) {
    console.warn('Failed to load NIMs:', err)
  }
}

const loadMore = () => {
  loadRequests(false)
}

const clearFilters = () => {
  filters.value = {
    status: 'all',
    requestType: 'all',
    nimId: 'all'
  }
  loadRequests()
}

const handleRequestClick = (request: InferenceRequest) => {
  // Navigate to request details or open in a modal
  console.log('Request clicked:', request)
  // TODO: Implement request details view
}

const handleRequestDelete = async (requestId: string) => {
  try {
    // Remove the request from the local list immediately for better UX
    const requestIndex = requests.value.findIndex(r => r.id === requestId)
    if (requestIndex !== -1) {
      requests.value.splice(requestIndex, 1)
    }

    // Show success message
    successMessage.value = 'Inference request deleted successfully'

    // Clear success message after 3 seconds
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)

    // Clear any existing error messages
    error.value = ''

  } catch (err) {
    console.error('Failed to handle delete:', err)
    error.value = 'Failed to delete inference request'
  }
}


// Lifecycle
onMounted(() => {
  loadRequests()
  loadNims()
})
</script>
