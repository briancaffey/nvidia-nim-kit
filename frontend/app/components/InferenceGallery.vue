<template>
  <div class="space-y-6">
    <!-- Search and Filter Controls -->
    <div class="bg-white dark:bg-[#181818] rounded-lg border border-gray-200 dark:border-gray-600 p-6">
      <div class="flex flex-wrap items-end gap-4">
        <!-- Search Bar -->
        <div class="flex-1 min-w-64">
          <div class="relative">
            <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              id="search"
              v-model="searchTerm"
              placeholder="Search inference requests..."
              class="pl-10"
              @input="debouncedSearch"
            />
          </div>
        </div>

        <!-- NIM ID Filter -->
        <div class="flex-1 min-w-64">
          <Select v-model="selectedNimIds" multiple>
            <SelectTrigger class="w-full">
              <SelectValue placeholder="Filter by NIM..." />
            </SelectTrigger>
            <SelectContent>
              <SelectItem
                v-for="nimId in availableNimIds"
                :key="nimId"
                :value="nimId"
              >
                {{ nimId }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <!-- Results per page -->
        <div class="w-40">
          <Select :model-value="pagination.limit.value" @update:model-value="(value) => pagination.setLimit(value as number)">
            <SelectTrigger class="w-full">
              <SelectValue :placeholder="`${pagination.limit.value} per page`" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem :value="5">5 per page</SelectItem>
              <SelectItem :value="10">10 per page</SelectItem>
              <SelectItem :value="25">25 per page</SelectItem>
              <SelectItem :value="50">50 per page</SelectItem>
              <SelectItem :value="100">100 per page</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <!-- Clear Filters Button -->
        <Button
          variant="outline"
          :disabled="!hasActiveFilters"
          @click="clearFilters"
        >
          Clear Filters
        </Button>
      </div>
    </div>

    <!-- Debug Section (hidden by default, can be enabled by setting showDebug = true) -->
    <div v-if="showDebug" class="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800 p-6">
      <h2 class="text-lg font-semibold mb-4 text-yellow-800 dark:text-yellow-200">Debug Info</h2>
      <div class="space-y-4">
        <div>
          <Button @click="loadInferenceRequests" :disabled="isLoading" variant="outline">
            {{ isLoading ? 'Loading...' : 'Reload Data' }}
          </Button>
        </div>

        <div v-if="error" class="text-red-600">
          Error: {{ error }}
        </div>

        <div v-if="rawData">
          <h3 class="font-medium mb-2">Raw API Data:</h3>
          <pre class="bg-gray-100 dark:bg-gray-900 p-4 rounded text-xs overflow-auto max-h-96">{{ rawData }}</pre>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="text-center py-12">
      <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-8">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
        <p class="text-gray-600 dark:text-gray-400">Loading inference requests...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-12">
      <div class="bg-red-50 dark:bg-red-900/20 rounded-lg p-8">
        <AlertCircle class="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-red-900 dark:text-red-100 mb-2">Error Loading Data</h3>
        <p class="text-red-700 dark:text-red-300 mb-4">{{ error }}</p>
        <Button @click="loadInferenceRequests">
          Try Again
        </Button>
      </div>
    </div>

    <!-- Results -->
    <div v-else-if="inferenceRequests.length > 0" class="space-y-4">
      <!-- Results Header -->
      <div class="flex justify-between items-center">
        <div class="text-sm text-gray-600 dark:text-gray-400">
          Showing {{ inferenceRequests.length }} of {{ pagination.total.value }} results
        </div>
        <div class="text-sm text-gray-600 dark:text-gray-400">
          Page {{ pagination.page.value }} of {{ pagination.totalPages.value }}
        </div>
      </div>

      <!-- Inference Request Cards -->
      <div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        <InferenceRequestCard
          v-for="request in inferenceRequests"
          :key="request.request_id"
          :request="request"
          @deleted="handleRequestDeleted"
        />
      </div>

      <!-- Pagination -->
      <div class="py-8">
        <Pagination
          :page="pagination.page.value"
          :total="pagination.total.value"
          :limit="pagination.limit.value"
          :total-pages="pagination.totalPages.value"
          :has-next-page="pagination.hasNextPage.value"
          :has-previous-page="pagination.hasPreviousPage.value"
          :set-page="pagination.setPage"
          :next-page="pagination.nextPage"
          :previous-page="pagination.previousPage"
          :first-page="pagination.firstPage"
          :last-page="pagination.lastPage"
        />
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-12">
      <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-8">
        <ImageIcon class="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">No inference requests found</h3>
        <p class="text-gray-600 dark:text-gray-400 mb-4">Click the button below to load inference requests.</p>
        <Button @click="loadInferenceRequests">
          Load Data
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { Search, AlertCircle, ImageIcon } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import InferenceRequestCard from '@/components/InferenceRequestCard.vue'
import Pagination from '@/components/Pagination.vue'
import { usePagination } from '~/composables/usePagination'

// Types
interface InferenceRequest {
  request_id: string
  type: string
  request_type: string
  nim_id: string
  model: string
  stream: boolean
  status: string
  date_created: string
  date_updated: string
  input_json: string
  output_json: string
  error_json: string
  input_data: any
  output_data: any
  error_data: any
}

// Reactive state
const isLoading = ref(false)
const error = ref('')
const inferenceRequests = ref<InferenceRequest[]>([])
const rawData = ref('')
const searchTerm = ref('')
const selectedNimIds = ref<string[]>([])
const availableNimIds = ref<string[]>([])
const showDebug = ref(false) // Set to true to show debug info

// Pagination
const pagination = usePagination({
  initialPage: 1,
  initialLimit: 10,
  onPageChange: () => {
    loadInferenceRequests()
  },
  onLimitChange: () => {
    loadInferenceRequests()
  }
})

// API configuration
const config = useRuntimeConfig()
const apiBase = config.public.apiBase

// Computed properties
const hasActiveFilters = computed(() => {
  return searchTerm.value.trim() !== '' || selectedNimIds.value.length > 0
})

// Debounced search function
let searchTimeout: ReturnType<typeof setTimeout> | null = null
const debouncedSearch = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(() => {
    loadInferenceRequests()
  }, 500) // 500ms delay
}

// Methods
const loadInferenceRequests = async () => {
  console.log('loadInferenceRequests called')
  isLoading.value = true
  error.value = ''

  try {
    // Build query parameters
    const params = new URLSearchParams({
      limit: pagination.limit.value.toString(),
      offset: pagination.offset.value.toString()
    })

    if (searchTerm.value.trim()) {
      params.append('search', searchTerm.value.trim())
    }

    if (selectedNimIds.value.length > 0) {
      params.append('nim_ids', selectedNimIds.value.join(','))
    }

    const url = `${apiBase}/api/gallery/inference-requests?${params}`
    console.log('Making request to:', url)

    const response = await fetch(url)
    console.log('Response status:', response.status)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
    }

    const data = await response.json()
    console.log('Received data:', data)

    // Store raw data for debugging
    rawData.value = JSON.stringify(data, null, 2)

    inferenceRequests.value = data.results || []

    // Update pagination total from API response
    if (data.pagination) {
      pagination.setTotal(data.pagination.total_count)
    }

  } catch (err) {
    console.error('Error loading inference requests:', err)
    error.value = `Failed to load inference requests: ${err}`
    inferenceRequests.value = []
  } finally {
    isLoading.value = false
  }
}

const loadInferenceRequestsSilently = async () => {
  // Same logic as loadInferenceRequests but without setting isLoading
  error.value = ''

  try {
    // Build query parameters
    const params = new URLSearchParams({
      limit: pagination.limit.value.toString(),
      offset: pagination.offset.value.toString()
    })

    if (searchTerm.value.trim()) {
      params.append('search', searchTerm.value.trim())
    }

    if (selectedNimIds.value.length > 0) {
      params.append('nim_ids', selectedNimIds.value.join(','))
    }

    const url = `${apiBase}/api/gallery/inference-requests?${params}`
    console.log('Making silent request to:', url)

    const response = await fetch(url)
    console.log('Silent response status:', response.status)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
    }

    const data = await response.json()
    console.log('Received silent data:', data)

    // Store raw data for debugging
    rawData.value = JSON.stringify(data, null, 2)

    inferenceRequests.value = data.results || []

    // Update pagination total from API response
    if (data.pagination) {
      pagination.setTotal(data.pagination.total_count)
    }

  } catch (err) {
    console.error('Error loading inference requests silently:', err)
    error.value = `Failed to load inference requests: ${err}`
    inferenceRequests.value = []
  }
}

const loadAvailableNimIds = async () => {
  try {
    console.log('Loading available NIM IDs from catalog...')
    const url = `${apiBase}/api/nims/catalog`
    console.log('Making request to:', url)

    const response = await fetch(url)
    console.log('NIM catalog response status:', response.status)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
    }

    const data = await response.json()
    console.log('Received NIM catalog data:', data)

    // Extract NIM IDs from the catalog data
    const nimIds = data.map((nim: any) => nim.id).filter((id: string) => id)
    availableNimIds.value = nimIds
    console.log('Extracted NIM IDs:', nimIds)

  } catch (err) {
    console.error('Failed to load NIM IDs:', err)
    availableNimIds.value = []
  }
}

const clearFilters = () => {
  searchTerm.value = ''
  selectedNimIds.value = []
  pagination.setPage(1)
  loadInferenceRequests()
}

const handleRequestDeleted = async (requestId: string) => {
  console.log('Request deleted:', requestId)
  // Reload the gallery data to reflect the deletion without showing loading state
  await loadInferenceRequestsSilently()
}

// Watch for changes in selected NIM IDs
watch(selectedNimIds, () => {
  pagination.setPage(1)
  loadInferenceRequests()
})

// Lifecycle - use nextTick to ensure component is fully mounted
onMounted(async () => {
  console.log('onMounted called, loading data...')
  await nextTick()
  loadAvailableNimIds()
  loadInferenceRequests()
})
</script>