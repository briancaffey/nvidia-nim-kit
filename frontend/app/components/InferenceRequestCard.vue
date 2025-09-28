<template>
  <Card class="h-full bg-white dark:bg-[#0a0a0a] rounded-lg group">
    <CardHeader class="pb-0">
      <div class="flex items-start justify-between">
        <div class="space-y-1">
          <CardTitle class="text-lg font-semibold truncate">
            {{ request.nim_id }}
          </CardTitle>
        </div>
        <!-- Status indicator that hides on hover, delete button that shows on hover -->
        <div class="relative">
          <!-- Green checkmark for completed status -->
          <div v-if="request.status === 'completed'" class="text-green-500 group-hover:opacity-0 transition-opacity duration-200">
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
            </svg>
          </div>
          <!-- Badge for other statuses -->
          <Badge v-else :variant="statusVariant" class="group-hover:opacity-0 transition-opacity duration-200">
            {{ request.status }}
          </Badge>

          <!-- Delete button that appears on hover -->
          <button
            @click="handleDelete"
            :disabled="isDeleting"
            class="absolute top-0 right-0 w-8 h-8 bg-red-500 hover:bg-red-600 text-white rounded-lg flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200 disabled:opacity-50 shadow-lg"
            title="Delete this request"
          >
            <svg
              v-if="!isDeleting"
              class="w-4 h-4"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M3 6h18l-2 13H5L3 6zM8 4v2H6V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v2h-2V4H8zM5 6l2 13h10l2-13H5z"/>
              <path d="M10 9v6M14 9v6"/>
            </svg>
            <svg
              v-else
              class="w-4 h-4 animate-spin"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </button>
        </div>
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

        <!-- Trellis (3D Model Generation) -->
        <TrellisCard
          v-else-if="isTrellisNim"
          :request="request"
        />

        <!-- Studio Voice (Speech Enhancement) -->
        <StudioVoiceCard
          v-else-if="isStudioVoiceNim"
          :request="request"
        />

        <!-- PaddleOCR (Text Detection) -->
        <PaddleOcrCard
          v-else-if="isPaddleOcrNim"
          :request="request"
        />

        <!-- Parakeet ASR (Speech Recognition) -->
        <ParakeetCard
          v-else-if="isParakeetNim"
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
import { computed, ref } from 'vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import SchnellCard from './SchnellCard.vue'
import TrellisCard from './TrellisCard.vue'
import StudioVoiceCard from './StudioVoiceCard.vue'
import PaddleOcrCard from './PaddleOcrCard.vue'
import ParakeetCard from './ParakeetCard.vue'

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

// Emits
const emit = defineEmits<{
  deleted: [requestId: string]
}>()

// Reactive state
const isDeleting = ref(false)

// Computed properties
const isSchnellNim = computed(() => {
  return props.request.nim_id.includes('flux_1-schnell') ||
         props.request.nim_id.includes('flux') ||
         props.request.type === 'IMAGE_GENERATION'
})

const isTrellisNim = computed(() => {
  return props.request.nim_id.includes('trellis') ||
         props.request.type === '3D_GENERATION' ||
         props.request.request_type === '3d_generation'
})

const isStudioVoiceNim = computed(() => {
  return props.request.nim_id.includes('studiovoice') ||
         props.request.type === 'SPEECH_ENHANCEMENT' ||
         props.request.request_type === 'speech_enhancement'
})

const isPaddleOcrNim = computed(() => {
  return props.request.nim_id.includes('paddleocr') ||
         props.request.nim_id.includes('baidu') ||
         props.request.type === 'TEXT_DETECTION' ||
         props.request.request_type === 'text_detection' ||
         props.request.nim_id.includes('ocr')
})

const isParakeetNim = computed(() => {
  return props.request.nim_id.includes('parakeet') ||
         props.request.nim_id.includes('asr') ||
         props.request.type === 'SPEECH_RECOGNITION' ||
         props.request.request_type === 'speech_recognition' ||
         props.request.nim_id.includes('riva')
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

const handleDelete = async () => {
  if (isDeleting.value) return

  isDeleting.value = true

  try {
    const config = useRuntimeConfig()
    const apiBase = config.public.apiBase

    const response = await fetch(`${apiBase}/api/gallery/inference-requests/${props.request.request_id}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Failed to delete request: ${response.statusText}`)
    }

    // Emit the deleted event to parent component
    emit('deleted', props.request.request_id)

  } catch (error) {
    console.error('Error deleting inference request:', error)
    // You could add a toast notification here if you have one
  } finally {
    isDeleting.value = false
  }
}
</script>
