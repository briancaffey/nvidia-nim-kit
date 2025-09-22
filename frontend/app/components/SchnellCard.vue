<template>
  <div>
    <!-- Generated Image -->
    <div v-if="imageUrl">
      <img
        :src="imageUrl"
        :alt="prompt"
        class="w-full object-contain rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800"
      />
    </div>

    <!-- Prompt -->
    <div v-if="prompt" class="py-2">
      <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
        <p class="text-sm text-gray-700 dark:text-gray-300 font-mono">{{ prompt }}</p>
      </div>
    </div>

    <!-- Generation Parameters as badges -->
    <div v-if="hasParameters" class="flex flex-wrap gap-2">
      <Badge v-if="parameters.width && parameters.height" variant="secondary" class="text-xs">
        {{ parameters.width }}×{{ parameters.height }}
      </Badge>
      <Badge v-if="parameters.steps" variant="outline" class="text-xs">
        {{ parameters.steps }} steps
      </Badge>
      <Badge v-if="parameters.guidance_scale" variant="outline" class="text-xs">
        CFG {{ parameters.guidance_scale }}
      </Badge>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Badge } from '@/components/ui/badge'

interface Props {
  request: {
    input_data: any
    output_data: any
  }
}

const props = defineProps<Props>()

// Extract data from request
const prompt = computed(() => {
  try {
    return props.request.input_data?.prompt || props.request.input_data?.text || ''
  } catch {
    return ''
  }
})

const imageUrl = computed(() => {
  try {
    const outputData = props.request.output_data

    // Check for artifacts array first (Schnell format)
    if (outputData?.artifacts && Array.isArray(outputData.artifacts) && outputData.artifacts.length > 0) {
      const artifact = outputData.artifacts[0]
      if (artifact?.base64 && typeof artifact.base64 === 'string') {
        // If it's already a data URL, return it
        if (artifact.base64.startsWith('data:image/')) {
          return artifact.base64
        }
        // If it's base64 data without the data URL prefix, add it
        if (artifact.base64.startsWith('/9j/') || artifact.base64.startsWith('iVBOR')) {
          return `data:image/png;base64,${artifact.base64}`
        }
      }
    }

    // Check for direct base64 image data
    if (outputData?.image && typeof outputData.image === 'string') {
      // If it's already a data URL, return it
      if (outputData.image.startsWith('data:image/')) {
        return outputData.image
      }
      // If it's base64 data without the data URL prefix, add it
      if (outputData.image.startsWith('/9j/') || outputData.image.startsWith('iVBOR')) {
        return `data:image/png;base64,${outputData.image}`
      }
    }

    // Check for other image URL formats
    return outputData?.image_url ||
           outputData?.url ||
           outputData?.image || ''
  } catch {
    return ''
  }
})

const parameters = computed(() => {
  try {
    return props.request.input_data || {}
  } catch {
    return {}
  }
})

const hasParameters = computed(() => {
  return parameters.value.width || parameters.value.height ||
         parameters.value.steps || parameters.value.guidance_scale
})
</script>