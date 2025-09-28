<template>
  <div class="word-timestamps">
    <!-- Simple Audio Player -->
    <div v-if="audioUrl" class="mb-6">
      <div class="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <audio
          ref="audioElement"
          :src="audioUrl"
          controls
          class="w-full"
          preload="metadata"
          @timeupdate="onTimeUpdate"
        >
          Your browser does not support the audio element.
        </audio>
      </div>
    </div>

    <!-- Word Display -->
    <div class="word-content">
      <template v-for="(word, index) in words" :key="index">
        <span
          :class="getWordClasses(word, index)"
          :style="getWordStyle(word, index)"
          @mouseenter="showTooltip(word, $event)"
          @mouseleave="hideTooltip"
          class="word-span cursor-pointer transition-all duration-200"
        >
          {{ word.word }}
        </span>
        <span class="word-separator"> </span>
      </template>
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

interface Word {
  word: string
  start_time: number
  end_time: number
  confidence?: number
}

interface Tooltip {
  visible: boolean
  word?: Word
  x: number
  y: number
}

const props = defineProps<{
  words: Word[]
  audioUrl?: string
}>()

const tooltip = ref<Tooltip>({
  visible: false,
  x: 0,
  y: 0
})

const audioElement = ref<HTMLAudioElement | null>(null)
const currentTime = ref(0) // Current time in milliseconds

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

const getWordClasses = (word: Word, index: number) => {
  const classes = ['word-span']

  // Add active class if current time is within the word's time range
  if (currentTime.value >= word.start_time && currentTime.value <= word.end_time) {
    classes.push('word-active')
  }

  return classes.join(' ')
}

// Simple hash function for better color distribution
const hashString = (str: string): number => {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash // Convert to 32-bit integer
  }
  return Math.abs(hash)
}

// Track word order for consistent color rotation
let wordCounter = 0
const wordColorMap = new Map<string, number>()

const getWordStyle = (word: Word, index: number) => {
  // Always provide basic spacing
  const baseStyle = {
    padding: '2px 4px',
    margin: '0 1px',
    color: 'black', // Default for colored words
    whiteSpace: 'pre-wrap', // Preserve spaces but allow wrapping
    wordBreak: 'break-word', // Allow breaking within words if needed
    transition: 'all 0.3s ease-in-out'
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

const tooltipStyle = computed(() => ({
  left: `${tooltip.value.x}px`,
  top: `${tooltip.value.y}px`,
  transform: 'translate(-50%, -100%)'
}))

const showTooltip = (word: Word, event: MouseEvent) => {
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

// Audio event handler
const onTimeUpdate = () => {
  if (audioElement.value) {
    // Convert seconds to milliseconds to match our timestamp format
    currentTime.value = audioElement.value.currentTime * 1000
  }
}

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

onMounted(() => {
  document.addEventListener('mousemove', handleMouseMove)
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
})
</script>

<style scoped>
.word-timestamps {
  width: 100%;
}

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

.word-span.word-active {
  filter: brightness(1.3);
  animation: wordBrighten 0.3s ease-in-out;
}

.word-span.word-active:hover {
  transform: scale(1.05);
}

@keyframes wordBrighten {
  0% { filter: brightness(1); }
  100% { filter: brightness(1.3); }
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

.dark .word-span.word-active {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.5);
}
</style>
