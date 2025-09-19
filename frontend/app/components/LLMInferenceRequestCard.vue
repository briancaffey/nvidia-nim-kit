<template>
  <Card class="hover:shadow-md transition-shadow cursor-pointer" @click="handleClick">
    <CardHeader class="pb-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <Badge :variant="statusVariant">{{ status }}</Badge>
          <Badge variant="outline">{{ requestType }}</Badge>
        </div>
        <div class="flex items-center space-x-2">
          <div class="text-sm text-gray-500 dark:text-gray-400">
            {{ formatDate(dateCreated) }}
          </div>
          <Button
            variant="outline"
            size="sm"
            class="h-8 px-2 text-blue-600 hover:text-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900/20"
            @click.stop="handleViewDetails"
          >
            <Icon name="lucide:eye" class="h-4 w-4 mr-1" />
            View
          </Button>
          <Button
            variant="ghost"
            size="sm"
            class="h-8 w-8 p-0 text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
            @click.stop="handleDelete"
            :disabled="deleting"
          >
            <Icon
              name="lucide:trash-2"
              class="h-4 w-4"
              :class="{ 'animate-spin': deleting }"
            />
          </Button>
        </div>
      </div>
    </CardHeader>

    <CardContent class="space-y-3">
      <!-- Model and NIM Info -->
      <div class="space-y-1">
        <div class="flex items-center space-x-2">
          <span class="text-sm font-medium">{{ model }}</span>
        </div>
        <div class="flex items-center space-x-2">
          <span class="text-sm text-gray-600 dark:text-gray-400">{{ nimId }}</span>
        </div>
      </div>


      <!-- Input JSON Debug -->
      <Accordion type="single" collapsible class="w-full">
        <AccordionItem value="input-json">
          <AccordionTrigger class="text-sm font-medium text-gray-700 dark:text-gray-300 hover:no-underline">
            <div class="flex items-center space-x-2">
              <Icon name="lucide:code" class="h-4 w-4" />
              <span>Input JSON</span>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <div class="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg border">
              <pre class="text-xs text-gray-600 dark:text-gray-400 overflow-x-auto whitespace-pre-wrap">{{ formattedInputJson }}</pre>
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>

      <!-- Output JSON Debug -->
      <Accordion type="single" collapsible class="w-full">
        <AccordionItem value="output-json">
          <AccordionTrigger class="text-sm font-medium text-gray-700 dark:text-gray-300 hover:no-underline">
            <div class="flex items-center space-x-2">
              <Icon name="lucide:file-text" class="h-4 w-4" />
              <span>Output JSON</span>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <div class="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg border">
              <pre class="text-xs text-gray-600 dark:text-gray-400 overflow-x-auto whitespace-pre-wrap">{{ formattedOutputJson }}</pre>
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>

      <!-- Response Preview -->
      <div v-if="hasResponse" class="space-y-2">
        <div class="text-sm font-medium text-gray-700 dark:text-gray-300">Response Preview:</div>
        <div class="text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 p-2 rounded border">
          {{ truncateText(responsePreview, 150) }}
        </div>
      </div>

      <!-- Error Preview -->
      <div v-if="hasError" class="space-y-2">
        <div class="text-sm font-medium text-red-700 dark:text-red-300">Error:</div>
        <div class="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded border">
          {{ truncateText(errorPreview, 150) }}
        </div>
      </div>

      <!-- Metadata -->
      <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
        <div class="flex items-center space-x-4">
          <span v-if="stream" class="flex items-center space-x-1">
            <Icon name="lucide:zap" class="h-3 w-3" />
            <span>Streaming</span>
            <span v-if="isStreamingResponse" class="text-blue-600 dark:text-blue-400">
              ({{ streamingChunkCount }} chunks)
            </span>
          </span>
          <span v-else class="flex items-center space-x-1">
            <Icon name="lucide:clock" class="h-3 w-3" />
            <span>Standard</span>
          </span>
        </div>
        <div>{{ formatDate(dateUpdated) }}</div>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'

interface Props {
  request: {
    id: string
    request_type: string
    nim_id: string
    model: string
    stream: boolean
    status: string
    date_created: string
    date_updated: string
    input?: any
    output?: any
    error?: any
  }
}

const props = defineProps<Props>()

const emit = defineEmits<{
  click: [request: Props['request']]
  delete: [requestId: string]
}>()

// Runtime config
const runtimeConfig = useRuntimeConfig()
const apiBase = runtimeConfig.public.apiBase

// Reactive state
const deleting = ref(false)

// Computed properties
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

const requestType = computed(() => {
  return props.request.request_type === 'chat' ? 'Chat' : 'Completion'
})


const formattedInputJson = computed(() => {
  try {
    return JSON.stringify(props.request.input, null, 2)
  } catch {
    return 'Invalid JSON'
  }
})

const formattedOutputJson = computed(() => {
  try {
    return JSON.stringify(props.request.output, null, 2)
  } catch {
    return 'Invalid JSON'
  }
})

const hasResponse = computed(() => {
  return props.request.output && !props.request.error
})

const hasError = computed(() => {
  // Only show error if there's actual error content
  return props.request.error &&
         props.request.error.error &&
         props.request.error.error.trim() !== ''
})

const responsePreview = computed(() => {
  // Handle streaming response format (new format with chunks array)
  if (props.request.output?.streaming && props.request.output?.chunks) {
    const chunks = props.request.output.chunks
    if (chunks.length > 0) {
      // Extract content from all chunks and concatenate
      let fullContent = ''
      for (const chunk of chunks) {
        if (chunk.choices?.[0]?.delta?.content) {
          fullContent += chunk.choices[0].delta.content
        } else if (chunk.choices?.[0]?.text) {
          fullContent += chunk.choices[0].text
        }
      }
      return fullContent
    }
    return `Streaming response with ${props.request.output.total_chunks || 0} chunks`
  }

  // Handle non-streaming response format (legacy format)
  if (props.request.output?.choices?.[0]?.message?.content) {
    return props.request.output.choices[0].message.content
  }
  if (props.request.output?.choices?.[0]?.text) {
    return props.request.output.choices[0].text
  }
  return ''
})

const errorPreview = computed(() => {
  if (props.request.error?.error) {
    return props.request.error.error
  }
  return ''
})

const stream = computed(() => {
  return props.request.stream
})

const isStreamingResponse = computed(() => {
  return props.request.output?.streaming === true && props.request.output?.chunks
})

const streamingChunkCount = computed(() => {
  return props.request.output?.total_chunks || 0
})

const dateCreated = computed(() => {
  return props.request.date_created
})

const dateUpdated = computed(() => {
  return props.request.date_updated
})

// Methods
const truncateText = (text: string, maxLength: number): string => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}


const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString)
    return date.toLocaleString()
  } catch {
    return dateString
  }
}

const handleClick = () => {
  emit('click', props.request)
}

const handleViewDetails = () => {
  // Navigate to the appropriate detail page based on request type
  const route = props.request.request_type === 'chat'
    ? `/llm/chat/${props.request.id}`
    : `/llm/completion/${props.request.id}`

  navigateTo(route)
}

const handleDelete = async () => {
  if (deleting.value) return

  deleting.value = true

  try {
    const response = await fetch(`${apiBase}/api/llm/inference/${props.request.id}`, {
      method: 'DELETE',
    })

    if (!response.ok) {
      throw new Error(`Failed to delete request: ${response.statusText}`)
    }

    // Emit delete event to parent component
    emit('delete', props.request.id)
  } catch (error) {
    console.error('Failed to delete inference request:', error)
    // You could emit an error event here if needed
  } finally {
    deleting.value = false
  }
}
</script>
