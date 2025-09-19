<template>
  <div class="container mx-auto px-4 py-8 max-w-6xl">
    <!-- Header -->
    <div class="mb-8">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Chat Request Details
          </h1>
          <p class="text-gray-600 dark:text-gray-400">
            Request ID: {{ requestId }}
          </p>
        </div>
        <div class="flex items-center space-x-4">
          <NuxtLink to="/llm/chat" class="text-blue-500 hover:underline">
            ← Back to Chat
          </NuxtLink>
          <Button variant="outline" @click="refreshData" :disabled="loading">
            <Icon name="lucide:refresh-cw" class="mr-2 h-4 w-4" :class="{ 'animate-spin': loading }" />
            Refresh
          </Button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="text-center">
        <Icon name="lucide:loader-2" class="h-8 w-8 animate-spin mx-auto mb-4 text-gray-500" />
        <p class="text-gray-600 dark:text-gray-400">Loading request details...</p>
      </div>
    </div>

    <!-- Error State -->
    <Alert v-else-if="error" variant="destructive" class="mb-6">
      <AlertTitle>Error</AlertTitle>
      <AlertDescription>{{ error }}</AlertDescription>
    </Alert>

    <!-- Request Details -->
    <div v-else-if="requestData" class="space-y-6">
      <!-- Request Info Card -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center space-x-2">
            <Icon name="lucide:info" class="h-5 w-5" />
            <span>Request Information</span>
          </CardTitle>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <Label class="text-sm font-medium text-gray-500 dark:text-gray-400">Request ID</Label>
              <p class="text-sm font-mono bg-gray-100 dark:bg-gray-800 p-2 rounded">{{ requestData.id }}</p>
            </div>
            <div>
              <Label class="text-sm font-medium text-gray-500 dark:text-gray-400">Status</Label>
              <Badge :variant="getStatusVariant(requestData.status)" class="mt-1">
                {{ requestData.status }}
              </Badge>
            </div>
            <div>
              <Label class="text-sm font-medium text-gray-500 dark:text-gray-400">NIM ID</Label>
              <p class="text-sm">{{ requestData.nim_id }}</p>
            </div>
            <div>
              <Label class="text-sm font-medium text-gray-500 dark:text-gray-400">Model</Label>
              <p class="text-sm">{{ requestData.model }}</p>
            </div>
            <div>
              <Label class="text-sm font-medium text-gray-500 dark:text-gray-400">Streaming</Label>
              <Badge :variant="requestData.stream ? 'default' : 'secondary'" class="mt-1">
                {{ requestData.stream ? 'Yes' : 'No' }}
              </Badge>
            </div>
            <div>
              <Label class="text-sm font-medium text-gray-500 dark:text-gray-400">Created</Label>
              <p class="text-sm">{{ formatDate(requestData.date_created) }}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Input Messages -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center space-x-2">
            <Icon name="lucide:message-square" class="h-5 w-5" />
            <span>Input Messages</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div v-if="requestData.input?.messages" class="space-y-4">
            <div
              v-for="(message, index) in requestData.input.messages"
              :key="index"
              class="border rounded-lg p-4"
              :class="message.role === 'user' ? 'bg-blue-50 dark:bg-blue-900/20' : 'bg-gray-50 dark:bg-gray-800'"
            >
              <div class="flex items-center space-x-2 mb-2">
                <Badge :variant="message.role === 'user' ? 'default' : 'secondary'">
                  {{ message.role }}
                </Badge>
                <span class="text-sm text-gray-500 dark:text-gray-400">Message {{ index + 1 }}</span>
              </div>
              <div class="whitespace-pre-wrap text-sm">{{ message.content }}</div>
            </div>
          </div>
          <div v-else class="text-gray-500 dark:text-gray-400 text-sm">
            No input messages found
          </div>
        </CardContent>
      </Card>

      <!-- Response -->
      <Card v-if="requestData.output">
        <CardHeader>
          <CardTitle class="flex items-center space-x-2">
            <Icon name="lucide:bot" class="h-5 w-5" />
            <span>Response</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div v-if="requestData.stream" class="space-y-4">
            <!-- Streaming Response -->
            <div class="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
              <div class="flex items-center space-x-2 mb-2">
                <Badge variant="outline">Streaming Response</Badge>
                <span class="text-sm text-gray-500 dark:text-gray-400">
                  {{ requestData.output.total_chunks }} chunks
                </span>
              </div>
              <div class="whitespace-pre-wrap text-sm">{{ getStreamingResponseText() }}</div>
            </div>

            <!-- Logprobs Visualization for Streaming -->
            <div v-if="streamingTokens.length > 0">
              <h4 class="text-lg font-medium mb-3">Token Probabilities</h4>
              <TokenVisualization :tokens="streamingTokens" />
            </div>
          </div>
          <div v-else class="space-y-4">
            <!-- Non-streaming Response -->
            <div class="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
              <div class="flex items-center space-x-2 mb-2">
                <Badge variant="outline">Non-streaming Response</Badge>
              </div>
              <div class="whitespace-pre-wrap text-sm">{{ getNonStreamingResponseText() }}</div>
            </div>

            <!-- Logprobs Visualization for Non-streaming -->
            <div v-if="nonStreamingTokens.length > 0">
              <h4 class="text-lg font-medium mb-3">Token Probabilities</h4>
              <TokenVisualization :tokens="nonStreamingTokens" />
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Error Information -->
      <Card v-if="requestData.error && Object.keys(requestData.error).length > 0">
        <CardHeader>
          <CardTitle class="flex items-center space-x-2 text-red-600 dark:text-red-400">
            <Icon name="lucide:alert-circle" class="h-5 w-5" />
            <span>Error Details</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg">
            <pre class="text-sm whitespace-pre-wrap">{{ JSON.stringify(requestData.error, null, 2) }}</pre>
          </div>
        </CardContent>
      </Card>

      <!-- Raw Data (Collapsible) -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center space-x-2">
            <Icon name="lucide:code" class="h-5 w-5" />
            <span>Raw Request Data</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Collapsible>
            <CollapsibleTrigger as-child>
              <Button variant="outline" class="w-full justify-between">
                <span>View Raw Data</span>
                <Icon name="lucide:chevron-down" class="h-4 w-4" />
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent class="mt-4">
              <div class="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg">
                <pre class="text-xs overflow-auto">{{ JSON.stringify(requestData, null, 2) }}</pre>
              </div>
            </CollapsibleContent>
          </Collapsible>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Label } from '@/components/ui/label'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import TokenVisualization from '@/components/TokenVisualization.vue'
import { parseLogprobsFromResponse, parseLogprobsFromStreamingChunks, extractTextFromTokens, type Token } from '@/composables/useLogprobs'

// Validate route parameter
definePageMeta({
  validate: async (route) => {
    // Check if the id parameter exists and is a valid UUID format
    const id = route.params.id as string
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
    return typeof id === 'string' && uuidRegex.test(id)
  }
})

// Runtime config
const runtimeConfig = useRuntimeConfig()
const apiBase = runtimeConfig.public.apiBase

const route = useRoute()
const requestId = computed(() => route.params.id as string)

const loading = ref(true)
const error = ref('')
const requestData = ref<any>(null)

const streamingTokens = ref<Token[]>([])
const nonStreamingTokens = ref<Token[]>([])

const fetchRequestData = async () => {
  try {
    loading.value = true
    error.value = ''

    const response = await $fetch(`${apiBase}/api/llm/inference/${requestId.value}`) as any
    requestData.value = response

    // Parse logprobs if available
    if (response.output) {
      if (response.stream && response.output.chunks) {
        // Parse streaming chunks
        streamingTokens.value = parseLogprobsFromStreamingChunks(response.output.chunks)
      } else if (response.output.choices) {
        // Parse non-streaming response
        nonStreamingTokens.value = parseLogprobsFromResponse(response.output)
      }
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to fetch request data'
    console.error('Error fetching request data:', err)
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  fetchRequestData()
}

const getStatusVariant = (status: string) => {
  switch (status) {
    case 'completed':
      return 'default'
    case 'pending':
      return 'secondary'
    case 'error':
      return 'destructive'
    default:
      return 'outline'
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}

const getStreamingResponseText = () => {
  if (!requestData.value?.output?.chunks) return ''

  // If we have tokens, use them to extract text with proper spacing
  if (streamingTokens.value.length > 0) {
    return extractTextFromTokens(streamingTokens.value)
  }

  // Fallback to raw text extraction
  let text = ''
  for (const chunk of requestData.value.output.chunks) {
    if (chunk.choices?.[0]?.delta?.content) {
      text += chunk.choices[0].delta.content
    }
  }
  return text
}

const getNonStreamingResponseText = () => {
  if (!requestData.value?.output?.choices?.[0]?.message?.content) return ''

  // If we have tokens, use them to extract text with proper spacing
  if (nonStreamingTokens.value.length > 0) {
    return extractTextFromTokens(nonStreamingTokens.value)
  }

  // Fallback to raw text extraction
  return requestData.value.output.choices[0].message.content
}

onMounted(() => {
  fetchRequestData()
})
</script>

