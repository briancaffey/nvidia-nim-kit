<template>
  <div class="space-y-4">
    <!-- Transcribed Text -->
    <div v-if="transcribedText">
      <h4 class="font-medium text-gray-900 dark:text-white mb-2">Transcribed Text</h4>
      <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
        <p class="text-sm text-gray-900 dark:text-gray-100">{{ transcribedText }}</p>
      </div>
    </div>

    <!-- Audio Player -->
    <div v-if="audioUrl" class="space-y-2">
      <h4 class="font-medium text-gray-900 dark:text-white">Audio</h4>
      <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
        <audio
          :src="audioUrl"
          controls
          class="w-full"
          preload="metadata"
        >
          Your browser does not support the audio element.
        </audio>
      </div>
    </div>

    <!-- Debug info for audio (remove in production) -->
    <div v-else class="space-y-2">
      <h4 class="font-medium text-gray-900 dark:text-white">Audio Debug</h4>
      <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
        <pre class="text-xs text-gray-600 dark:text-gray-400 whitespace-pre-wrap">{{ JSON.stringify(debugInfo, null, 2) }}</pre>
      </div>
    </div>

    <!-- Word-level Timestamps -->
    <div v-if="words && words.length > 0" class="space-y-2">
      <h4 class="font-medium text-gray-900 dark:text-white">Word-level Timestamps</h4>
      <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
        <div class="word-content">
          <template v-for="(word, index) in words" :key="index">
            <span
              :style="getWordStyle(word, index)"
              @mouseenter="showTooltip(word, $event)"
              @mouseleave="hideTooltip"
              class="word-span cursor-pointer"
            >
              {{ word.word }}
            </span>
            <span class="word-separator"> </span>
          </template>
        </div>
      </div>
    </div>

    <!-- Tooltip -->
    <div
      v-if="tooltip.visible"
      :style="tooltipStyle"
      class="fixed z-50 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-3 max-w-xs"
    >
      <div class="flex items-center mb-2">
        <span class="font-medium text-gray-900 dark:text-white">{{ tooltip.word?.word }}</span>
      </div>
      <div class="space-y-1">
        <div class="flex justify-between items-center text-xs text-gray-600 dark:text-gray-400">
          <span>Start:</span>
          <span class="font-mono">{{ formatTimestamp(tooltip.word?.start_time || 0) }}</span>
        </div>
        <div class="flex justify-between items-center text-xs text-gray-600 dark:text-gray-400">
          <span>End:</span>
          <span class="font-mono">{{ formatTimestamp(tooltip.word?.end_time || 0) }}</span>
        </div>
        <div v-if="tooltip.word?.confidence !== undefined" class="flex justify-between items-center text-xs text-gray-600 dark:text-gray-400">
          <span>Confidence:</span>
          <span class="font-mono">{{ Math.round((tooltip.word?.confidence || 0) * 100) }}%</span>
        </div>
        <div class="flex justify-between items-center text-xs text-gray-600 dark:text-gray-400">
          <span>Duration:</span>
          <span class="font-mono">{{ formatDuration((tooltip.word?.end_time || 0) - (tooltip.word?.start_time || 0)) }}</span>
        </div>
      </div>
    </div>

    <!-- Confidence Score -->
    <div v-if="confidence !== undefined" class="space-y-2">
      <h4 class="font-medium text-gray-900 dark:text-white">Confidence Score</h4>
      <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
        <div class="flex items-center space-x-2">
          <div class="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              class="bg-green-500 h-2 rounded-full"
              :style="{ width: `${confidence * 100}%` }"
            ></div>
          </div>
          <span class="text-sm text-gray-600 dark:text-gray-300">
            {{ Math.round(confidence * 100) }}%
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'

interface Props {
  request: {
    input_data: any
    output_data: any
  }
}

interface Tooltip {
  visible: boolean
  word?: any
  x: number
  y: number
}

const props = defineProps<Props>()

const tooltip = ref<Tooltip>({
  visible: false,
  x: 0,
  y: 0
})

// Same color palette as TokenVisualization for consistency
const pastelColors = [
  'rgba(255, 105, 135, 0.9)', // Darker pink
  'rgba(255, 165, 100, 0.9)', // Darker peach/orange
  'rgba(255, 215, 0, 0.9)', // Darker yellow/gold
  'rgba(50, 205, 50, 0.9)', // Darker green
  'rgba(70, 130, 180, 0.9)', // Darker blue
  'rgba(186, 85, 211, 0.9)', // Darker purple
  'rgba(255, 20, 147, 0.9)', // Darker pink/magenta
  'rgba(255, 140, 0, 0.9)', // Darker orange
  'rgba(255, 99, 71, 0.9)', // Darker coral
  'rgba(255, 160, 122, 0.9)', // Darker salmon
  'rgba(138, 43, 226, 0.9)', // Darker violet
  'rgba(255, 182, 193, 0.9)', // Medium pink
  'rgba(144, 238, 144, 0.9)', // Medium green
  'rgba(255, 218, 185, 0.9)', // Medium peach
  'rgba(255, 192, 203, 0.9)', // Medium pink
  'rgba(173, 216, 230, 0.9)', // Medium blue
  'rgba(221, 160, 221, 0.9)', // Medium plum
  'rgba(255, 228, 196, 0.9)', // Medium bisque
  'rgba(240, 248, 255, 0.9)', // Medium alice blue
  'rgba(255, 239, 213, 0.9)', // Medium papaya whip
]

// Extract data from request
const transcribedText = computed(() => {
  try {
    return props.request.output_data?.text || ''
  } catch {
    return ''
  }
})

const words = computed(() => {
  try {
    return props.request.output_data?.words || []
  } catch {
    return []
  }
})

const confidence = computed(() => {
  try {
    return props.request.output_data?.confidence
  } catch {
    return undefined
  }
})

// Debug computed property to see what's in the input data
const debugInfo = computed(() => {
  try {
    const audioFilePath = props.request.input_data?.audio_file_path
    const config = useRuntimeConfig()

    return {
      hasInputData: !!props.request.input_data,
      inputKeys: Object.keys(props.request.input_data || {}),
      audioFilePath: audioFilePath,
      audioFilePathType: typeof audioFilePath,
      constructedUrl: audioFilePath ? `${config.public.apiBase}${audioFilePath.replace('/app/nimkit', '')}` : null,
      apiBase: config.public.apiBase
    }
  } catch {
    return { error: 'Failed to parse input data' }
  }
})

const audioUrl = computed(() => {
  try {
    // Get audio file path from input data
    const audioFilePath = props.request.input_data?.audio_file_path

    if (audioFilePath && typeof audioFilePath === 'string') {
      // Strip off /app/nimkit from the path to get the relative path
      const relativePath = audioFilePath.replace('/app/nimkit', '')

      // Construct the backend URL
      const config = useRuntimeConfig()
      const backendUrl = config.public.apiBase || ''

      return `${backendUrl}${relativePath}`
    }

    return null
  } catch (error) {
    console.error('Error extracting audio URL:', error)
    return null
  }
})

// Track word order for consistent color rotation
let wordCounter = 0
const wordColorMap = new Map<string, number>()

const getWordStyle = (word: any, index: number) => {
  // Always provide basic spacing
  const baseStyle = {
    padding: '2px 4px',
    margin: '0 1px',
    color: 'black', // Default for colored words
    whiteSpace: 'pre-wrap', // Preserve spaces but allow wrapping
    wordBreak: 'break-word', // Allow breaking within words if needed
    transition: 'all 0.2s ease-in-out'
  }

  // Use consistent color mapping for the same word text
  let colorIndex: number
  if (wordColorMap.has(word.word)) {
    colorIndex = wordColorMap.get(word.word)!
  } else {
    // Rotate through colors for new words
    colorIndex = wordCounter % pastelColors.length
    wordColorMap.set(word.word, colorIndex)
    wordCounter++
  }

  return {
    ...baseStyle,
    backgroundColor: pastelColors[colorIndex],
    borderRadius: '2px',
    border: '1px solid rgba(0, 0, 0, 0.1)',
    boxShadow: '0 1px 2px rgba(0, 0, 0, 0.1)'
  }
}

// Tooltip functions
const tooltipStyle = computed(() => ({
  left: `${tooltip.value.x}px`,
  top: `${tooltip.value.y}px`,
  transform: 'translate(-50%, -100%)'
}))

const showTooltip = (word: any, event: MouseEvent) => {
  tooltip.value = {
    visible: true,
    word,
    x: event.clientX,
    y: event.clientY - 10
  }
}

const hideTooltip = () => {
  tooltip.value.visible = false
}

// Handle mouse movement to update tooltip position
const handleMouseMove = (event: MouseEvent) => {
  if (tooltip.value.visible) {
    tooltip.value.x = event.clientX
    tooltip.value.y = event.clientY - 10
  }
}

// Formatting functions
const formatTimestamp = (milliseconds: number): string => {
  // Convert milliseconds to seconds for formatting
  const seconds = milliseconds / 1000
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  const ms = Math.floor((seconds % 1) * 1000)
  return `${mins}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`
}

const formatDuration = (milliseconds: number): string => {
  // Input is already in milliseconds, just format it nicely
  if (milliseconds < 1000) {
    return `${Math.round(milliseconds)}ms`
  } else {
    const seconds = milliseconds / 1000
    return `${seconds.toFixed(2)}s`
  }
}

// Lifecycle hooks
onMounted(() => {
  document.addEventListener('mousemove', handleMouseMove)
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
})
</script>

<style scoped>
.word-content {
  font-size: 0.875rem;
  line-height: 2; /* Increased line height for more spacing between lines */
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
  white-space: pre-wrap; /* Preserve whitespace and wrap text */
  word-wrap: break-word; /* Allow breaking long words */
  overflow-wrap: break-word; /* Modern property for word breaking */
}

.word-span {
  display: inline;
  transition: all 0.2s ease-in-out;
  white-space: pre-wrap; /* Preserve spaces but allow wrapping */
  word-break: break-word; /* Allow breaking within words if needed */
}

.word-span:hover {
  transform: scale(1.05);
}

.word-separator {
  margin-right: 2px;
}

/* Dark mode adjustments */
.dark .word-span {
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.dark .word-span:hover {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
}
</style>
