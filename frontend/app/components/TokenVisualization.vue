<template>
  <div class="token-visualization">
    <!-- Controls -->
    <div class="flex items-center justify-between mb-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
      <div class="flex items-center space-x-4">
        <div class="flex items-center space-x-2">
          <Switch
            id="show-colors"
            v-model="showColors"
          />
          <Label for="show-colors" class="text-sm">Show Token Colors</Label>
        </div>
        <div class="text-sm text-gray-600 dark:text-gray-400">
          {{ tokens.length }} tokens
        </div>
      </div>
      <div class="text-xs text-gray-500 dark:text-gray-500">
        Hover over tokens to see alternatives
      </div>
    </div>

    <!-- Token Display -->
    <div class="token-content">
      <template v-for="(token, index) in tokens" :key="index">
        <span
          :class="getTokenClasses(token)"
          :style="getTokenStyle(token)"
          @mouseenter="showTooltip(token, $event)"
          @mouseleave="hideTooltip"
          class="token-span cursor-pointer transition-all duration-200"
        >
          {{ cleanTokenText(token.text) }}
        </span>
        <br v-if="token.text.includes('Ċ')" />
      </template>
    </div>

    <!-- Tooltip -->
    <div
      v-if="tooltip.visible"
      :style="tooltipStyle"
      class="fixed z-50 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-3 max-w-xs"
    >
      <div class="flex items-center mb-2">
        <span class="text-sm font-medium text-gray-900 dark:text-white mr-2">Token:</span>
        <pre class="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-xs font-mono whitespace-pre inline">{{ cleanTokenText(tooltip.token?.text || '') }}</pre>
      </div>
      <div class="space-y-1">
        <div
          v-for="(alt, idx) in tooltip.token?.top_logprobs || []"
          :key="idx"
          class="flex justify-between items-center text-xs"
          :class="idx === 0 ? 'font-medium text-gray-900 dark:text-white' : 'text-gray-600 dark:text-gray-400'"
        >
          <pre class="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-xs font-mono mr-2 whitespace-pre">{{ cleanTokenText(alt.token) }}</pre>
          <span class="text-gray-500 dark:text-gray-500">{{ alt.logprob.toFixed(3) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'

interface LogprobAlternative {
  token: string
  logprob: number
}

interface Token {
  text: string
  logprob?: number
  top_logprobs?: LogprobAlternative[]
}

interface Tooltip {
  visible: boolean
  token?: Token
  x: number
  y: number
}

const props = defineProps<{
  tokens: Token[]
}>()

const showColors = ref(true)
const tooltip = ref<Tooltip>({
  visible: false,
  x: 0,
  y: 0
})

// Darker pastel colors for better text contrast (no grays!)
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

const getTokenClasses = (token: Token) => {
  const classes = ['token-span']

  if (showColors.value && token.logprob !== undefined) {
    classes.push('has-logprob')
  }

  return classes.join(' ')
}

// Clean token text by replacing GPT-2/BPE markers
const cleanTokenText = (text: string): string => {
  return text
    .replace(/Ġ/g, ' ')  // Replace Ġ with space
    .replace(/Ċ/g, '')   // Remove Ċ (we handle newlines with <br> tags)
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

// Track token order for consistent color rotation
let tokenCounter = 0
const tokenColorMap = new Map<string, number>()

const getTokenStyle = (token: Token) => {
  // Always provide basic spacing, even when colors are disabled
  const baseStyle = {
    padding: '2px 4px',
    margin: '0 1px',
    color: 'black', // Default for colored tokens
    whiteSpace: 'pre-wrap', // Preserve spaces but allow wrapping
    wordBreak: 'break-word' // Allow breaking within tokens if needed
  }

  if (!showColors.value || token.logprob === undefined) {
    // When colors are disabled, use theme-appropriate text color
    return {
      ...baseStyle,
      color: 'inherit' // This will inherit the theme's text color (white in dark mode, black in light mode)
    }
  }

  // Use consistent color mapping for the same token text
  let colorIndex: number
  if (tokenColorMap.has(token.text)) {
    colorIndex = tokenColorMap.get(token.text)!
  } else {
    // Rotate through colors for new tokens
    colorIndex = tokenCounter % pastelColors.length
    tokenColorMap.set(token.text, colorIndex)
    tokenCounter++
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

const showTooltip = (token: Token, event: MouseEvent) => {
  if (!token.top_logprobs || token.top_logprobs.length === 0) {
    return
  }

  tooltip.value = {
    visible: true,
    token,
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

onMounted(() => {
  document.addEventListener('mousemove', handleMouseMove)
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
})
</script>

<style scoped>
.token-visualization {
  width: 100%;
}

.token-content {
  font-size: 0.875rem;
  line-height: 2; /* Increased line height for more spacing between lines */
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
  white-space: pre-wrap; /* Preserve whitespace and wrap text */
  word-wrap: break-word; /* Allow breaking long words */
  overflow-wrap: break-word; /* Modern property for word breaking */
}

.token-span {
  display: inline;
  transition: all 0.2s ease;
  white-space: pre-wrap; /* Preserve spaces but allow wrapping */
  word-break: break-word; /* Allow breaking within tokens if needed */
}

.token-span:hover {
  transform: scale(1.05);
}

.token-span.has-logprob:hover {
  box-shadow: 0 2px 4px 0 rgb(0 0 0 / 0.15);
  transform: scale(1.05);
}

/* Dark mode adjustments */
.dark .token-span.has-logprob {
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.dark .token-span.has-logprob:hover {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
}
</style>
