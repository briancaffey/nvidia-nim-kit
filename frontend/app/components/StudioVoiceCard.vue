<template>
  <div class="space-y-4">
    <!-- Processing Info Badges -->
    <div class="flex flex-wrap gap-2">
      <!-- Model Type Badge -->
      <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
        {{ request.output_data?.model_type || 'N/A' }}
      </span>

      <!-- API Type Badge -->
      <span v-if="request.output_data?.api_type === 'nvidia_cloud'" class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
        NVIDIA Cloud
      </span>
      <span v-else-if="request.output_data?.api_type === 'local_nim'" class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
        Local NIM
      </span>

      <!-- Processing Time Badge -->
      <span v-if="request.output_data?.processing_time_seconds" class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200">
        {{ request.output_data.processing_time_seconds.toFixed(2) }}s
      </span>

      <!-- Sample Rate Badge -->
      <span v-if="request.output_data?.sample_rate" class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200">
        {{ request.output_data.sample_rate }} Hz
      </span>
    </div>

    <!-- Audio Players -->
    <div class="space-y-3">
      <!-- Enhanced Audio Player -->
      <div v-if="request.output_data?.enhanced_audio_path">
        <Label class="text-sm font-medium text-gray-900 dark:text-white">Enhanced Audio</Label>
        <div class="mt-1 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <audio
            :src="getAudioUrl(request.output_data.enhanced_audio_path)"
            controls
            class="w-full"
          >
            Your browser does not support the audio element.
          </audio>
        </div>
      </div>

      <!-- Original Audio Player -->
      <div v-if="request.output_data?.input_file">
        <Label class="text-sm font-medium text-gray-900 dark:text-white">Original Audio</Label>
        <div class="mt-1 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <audio
            :src="getOriginalAudioUrl(request.output_data.input_file)"
            controls
            class="w-full"
          >
            Your browser does not support the audio element.
          </audio>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Label } from '@/components/ui/label'

// Props
interface Props {
  request: {
    request_id: string
    output_data?: {
      model_type?: string
      api_type?: string
      processing_time_seconds?: number
      sample_rate?: number
      enhanced_audio_path?: string
      input_file?: string
    }
  }
}

const props = defineProps<Props>()

// Get runtime config for API base URL
const config = useRuntimeConfig()

// Methods
const getAudioUrl = (audioPath: string) => {
  // Convert the file path to a URL that can be accessed by the frontend
  const fileName = audioPath.split('/').pop()
  return `${config.public.apiBase}/media/studiovoice/output/${fileName}`
}

const getOriginalAudioUrl = (audioPath: string) => {
  // Convert the file path to a URL that can be accessed by the frontend
  const fileName = audioPath.split('/').pop()
  return `${config.public.apiBase}/media/studiovoice/input/${fileName}`
}
</script>
