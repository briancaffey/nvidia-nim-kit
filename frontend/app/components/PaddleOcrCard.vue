<template>
  <div class="space-y-4">
    <!-- Visualization Image -->
    <div v-if="hasVisualization" class="space-y-2">
      <div class="flex items-center justify-between">
        <h4 class="font-medium text-gray-900 dark:text-white">Text Detection Results</h4>
        <div class="flex gap-2">
          <Badge variant="secondary">
            {{ totalImages }} image{{ totalImages !== 1 ? 's' : '' }}
          </Badge>
          <Badge variant="outline">
            {{ totalDetections }} text region{{ totalDetections !== 1 ? 's' : '' }}
          </Badge>
        </div>
      </div>

      <div class="relative">
        <img
          :src="getVisualizationUrl(outputData.visualization_path)"
          alt="Text Detection Visualization"
          class="max-w-full h-auto rounded-lg border border-gray-200 dark:border-gray-600"
        />
        <div class="absolute top-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
          Blue boxes show detected text regions
        </div>
      </div>
    </div>

    <!-- No Visualization Fallback -->
    <div v-else-if="hasData" class="space-y-3">
      <div class="flex items-center justify-between">
        <h4 class="font-medium text-gray-900 dark:text-white">Text Detection Results</h4>
        <div class="flex gap-2">
          <Badge variant="secondary">
            {{ totalImages }} image{{ totalImages !== 1 ? 's' : '' }}
          </Badge>
          <Badge variant="outline">
            {{ totalDetections }} text region{{ totalDetections !== 1 ? 's' : '' }}
          </Badge>
        </div>
      </div>
    </div>

    <!-- No Results -->
    <div v-else class="text-center py-6 text-gray-500 dark:text-gray-400">
      <Icon name="lucide:file-x" class="h-8 w-8 mx-auto mb-2" />
      <p>No text detection results available</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Badge } from '@/components/ui/badge'

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

// Runtime config
const config = useRuntimeConfig()

// Computed properties
const outputData = computed(() => props.request.output_data || {})

const hasData = computed(() => {
  return outputData.value && outputData.value.data && Array.isArray(outputData.value.data) && outputData.value.data.length > 0
})

const hasVisualization = computed(() => {
  return hasData.value && outputData.value.visualization_path
})

const totalImages = computed(() => {
  if (!hasData.value) return 0
  return outputData.value.data.length
})

const totalDetections = computed(() => {
  if (!hasData.value) return 0
  return outputData.value.data.reduce((total: number, imageData: any) => {
    return total + (imageData.text_detections?.length || 0)
  }, 0)
})

// Methods
const getVisualizationUrl = (path: string): string => {
  // Convert backend path to frontend URL
  const relativePath = path.replace(/^.*\/media\//, '/media/')
  return `${config.public.apiBase}${relativePath}`
}
</script>
