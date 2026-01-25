<template>
  <div class="space-y-4">
    <!-- Processing Info Badges -->
    <div class="flex flex-wrap gap-2">
      <!-- Language Badge -->
      <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
        {{ getLanguageName(request.output_data?.language) }}
      </span>

      <!-- Voice Badge -->
      <span v-if="request.output_data?.voice" class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
        {{ getVoiceDisplayName(request.output_data.voice) }}
      </span>

      <!-- Sample Rate Badge -->
      <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
        {{ request.output_data?.sample_rate_hz || 22050 }} Hz
      </span>

      <!-- File Size Badge -->
      <span v-if="request.output_data?.audio_size_bytes" class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200">
        {{ formatFileSize(request.output_data.audio_size_bytes) }}
      </span>

      <!-- API Type Badge -->
      <span v-if="request.output_data?.api_type === 'nvidia_cloud'" class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200">
        NVIDIA Cloud
      </span>
      <span v-else-if="request.output_data?.api_type === 'local_nim'" class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200">
        Local NIM
      </span>
    </div>

    <!-- Audio Player -->
    <div v-if="request.output_data?.audio_path" class="space-y-2">
      <h4 class="font-medium text-gray-900 dark:text-white">Generated Audio</h4>
      <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
        <audio
          :src="getAudioUrl(request.output_data.audio_path)"
          controls
          class="w-full"
          preload="metadata"
        >
          Your browser does not support the audio element.
        </audio>
      </div>
    </div>

    <!-- Synthesized Text -->
    <div v-if="request.output_data?.text || request.input_data?.text">
      <h4 class="font-medium text-gray-900 dark:text-white mb-2">Text</h4>
      <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
        <p class="text-sm text-gray-900 dark:text-gray-100 line-clamp-3">
          {{ request.output_data?.text || request.input_data?.text }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Props
interface Props {
  request: {
    request_id: string
    input_data?: {
      text?: string
      language?: string
      voice?: string
      sample_rate_hz?: number
    }
    output_data?: {
      text?: string
      language?: string
      voice?: string
      sample_rate_hz?: number
      audio_path?: string
      audio_size_bytes?: number
      api_type?: string
    }
  }
}

const props = defineProps<Props>()

// Get runtime config for API base URL
const config = useRuntimeConfig()

// Language mapping
const languages: Record<string, string> = {
  'en-US': 'English (US)',
  'es-US': 'Spanish (US)',
  'fr-FR': 'French (France)',
  'de-DE': 'German (Germany)',
  'zh-CN': 'Chinese (Simplified)',
  'vi-VN': 'Vietnamese',
  'it-IT': 'Italian',
}

// Methods
const getLanguageName = (code: string | undefined) => {
  if (!code) return 'Unknown'
  return languages[code] || code
}

const getVoiceDisplayName = (voiceName: string) => {
  // Extract just the voice name from the full name
  // e.g., "Magpie-Multilingual.EN-US.Aria" -> "Aria"
  const parts = voiceName.split('.')
  return parts[parts.length - 1] || voiceName
}

const getAudioUrl = (audioPath: string) => {
  // Convert the file path to a URL that can be accessed by the frontend
  const fileName = audioPath.split('/').pop()
  return `${config.public.apiBase}/media/tts/output/${fileName}`
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
</script>
