<template>
  <Card class="h-full bg-white dark:bg-[#0a0a0a] rounded-lg">
    <CardHeader class="pb-0">
      <div class="flex items-start justify-between">
        <div class="space-y-1">
          <CardTitle class="text-lg font-semibold truncate">
            {{ request.nim_id }}
          </CardTitle>
        </div>
        <!-- Green checkmark for completed status -->
        <div v-if="request.status === 'completed'" class="text-green-500">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
          </svg>
        </div>
        <Badge v-else :variant="statusVariant">
          {{ request.status }}
        </Badge>
      </div>
    </CardHeader>

    <CardContent class="space-y-4">
      <!-- Content based on NIM type -->
      <div>
        <!-- Schnell (Image Generation) -->
        <SchnellCard
          v-if="isSchnellNim"
          :request="request"
        />

        <!-- Other NIM types - placeholder for now -->
        <div v-else class="space-y-3">
          <div class="text-sm">
            <h4 class="font-medium text-gray-900 dark:text-white mb-2">Input Data</h4>
            <div class="bg-gray-50 dark:bg-gray-800 rounded p-3 max-h-32 overflow-y-auto">
              <pre class="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{{ formatJson(request.input_data) }}</pre>
            </div>
          </div>

          <div v-if="request.output_data && Object.keys(request.output_data).length > 0" class="text-sm">
            <h4 class="font-medium text-gray-900 dark:text-white mb-2">Output Data</h4>
            <div class="bg-gray-50 dark:bg-gray-800 rounded p-3 max-h-32 overflow-y-auto">
              <pre class="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{{ formatJson(request.output_data) }}</pre>
            </div>
          </div>

          <div v-if="request.error_data && Object.keys(request.error_data).length > 0" class="text-sm">
            <h4 class="font-medium text-red-600 dark:text-red-400 mb-2">Error Data</h4>
            <div class="bg-red-50 dark:bg-red-900/20 rounded p-3 max-h-32 overflow-y-auto">
              <pre class="text-xs text-red-700 dark:text-red-300 whitespace-pre-wrap">{{ formatJson(request.error_data) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import SchnellCard from './SchnellCard.vue'

// Props
interface Props {
  request: {
    request_id: string
    type: string
    request_type: string
    nim_id: string
    model: string
    stream: boolean
    status: string
    date_created: string
    date_updated: string
    input_data: any
    output_data: any
    error_data: any
  }
}

const props = defineProps<Props>()

// Computed properties
const isSchnellNim = computed(() => {
  return props.request.nim_id.includes('flux_1-schnell') ||
         props.request.nim_id.includes('flux') ||
         props.request.type === 'IMAGE_GENERATION'
})

const statusVariant = computed(() => {
  switch (props.request.status) {
    case 'completed':
      return 'default'
    case 'pending':
      return 'secondary'
    case 'error':
      return 'destructive'
    default:
      return 'outline'
  }
})

// Methods
const formatJson = (data: any) => {
  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return String(data)
  }
}
</script>
