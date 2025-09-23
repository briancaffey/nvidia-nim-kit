<template>
  <div class="container mx-auto px-4 py-8 max-w-4xl">
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
        LLM Completion
      </h1>
      <p class="text-gray-600 dark:text-gray-400">
        Configure and run LLM completion requests
      </p>
      <NuxtLink to="/llm" class="text-blue-500 hover:underline">← Back to LLM</NuxtLink>
    </div>

    <!-- Error Alert -->
    <Alert v-if="error" variant="destructive" class="mb-6">
      <AlertTitle>Error</AlertTitle>
      <AlertDescription>{{ error }}</AlertDescription>
    </Alert>

    <!-- Success Alert -->
    <Alert v-if="successMessage" variant="default" class="mb-6">
      <AlertTitle>Success</AlertTitle>
      <AlertDescription>{{ successMessage }}</AlertDescription>
    </Alert>

    <!-- Main Completion Panel -->
    <Card class="mb-8">
      <CardHeader class="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Text Completion</CardTitle>
          <CardDescription>
            {{ selectedNimId ? `Connected to: ${selectedNimId}` : 'Configure NIM to start completion' }}
          </CardDescription>
        </div>
        <Button variant="outline" @click="showConfigModal = true">
          <Icon name="lucide:settings" class="mr-2 h-4 w-4" />
          Configure
        </Button>
      </CardHeader>
      <CardContent class="space-y-6">
        <!-- Prompt Input -->
        <div class="space-y-2">
          <Label for="prompt">Prompt</Label>
          <Textarea
            id="prompt"
            v-model="prompt"
            placeholder="Enter your prompt here..."
            rows="8"
          />
        </div>

        <!-- Submit Button -->
        <Button
          @click="runCompletion"
          :disabled="!canRunCompletion || isLoading"
          class="w-full"
          size="lg"
        >
          <Icon name="lucide:loader-2" v-if="isLoading" class="mr-2 h-4 w-4 animate-spin" />
          {{ isLoading ? 'Running Completion...' : 'Generate Completion' }}
        </Button>
      </CardContent>
    </Card>

    <!-- Configuration Modal -->
    <Dialog v-model:open="showConfigModal">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle>Configuration</DialogTitle>
          <DialogDescription>
            Configure NIM and completion parameters
          </DialogDescription>
        </DialogHeader>
        <div class="space-y-6">
          <!-- NIM Selection -->
          <div class="space-y-2">
            <Label for="nim-select">NIM Instance</Label>
            <Select v-model="selectedNimId" @update:model-value="onNimChange">
              <SelectTrigger>
                <SelectValue placeholder="Select a NIM instance" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem
                  v-for="nimId in nimIds"
                  :key="nimId"
                  :value="nimId"
                >
                  {{ nimId }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <!-- Model Selection -->
          <div class="space-y-2">
            <Label for="model">Model</Label>
            <div class="relative">
              <Input
                id="model"
                v-model="config.model"
                placeholder="e.g., llama-3.1-8b-instruct"
                :disabled="isLoadingModels"
              />
              <Icon name="lucide:loader-2" v-if="isLoadingModels" class="absolute right-3 top-3 h-4 w-4 animate-spin" />
            </div>
          </div>

          <!-- Temperature -->
          <div class="space-y-2">
            <Label for="temperature">Temperature</Label>
            <Input
              id="temperature"
              v-model.number="config.temperature"
              type="number"
              min="0"
              max="2"
              step="0.1"
              placeholder="0.7"
            />
          </div>

          <!-- Max Tokens -->
          <div class="space-y-2">
            <Label for="max-tokens">Max Tokens</Label>
            <Input
              id="max-tokens"
              v-model.number="config.max_tokens"
              type="number"
              placeholder="2048"
            />
          </div>

          <!-- Stream Toggle -->
          <div class="flex items-center space-x-2">
            <Switch
              id="stream"
              v-model="config.stream"
            />
            <Label for="stream">Stream Response</Label>
          </div>

          <!-- Logprobs Toggle -->
          <div class="flex items-center space-x-2">
            <Switch
              id="logprobs"
              v-model="config.logprobs"
            />
            <Label for="logprobs">Enable Logprobs</Label>
          </div>

          <!-- Top Logprobs -->
          <div v-if="config.logprobs" class="space-y-2">
            <Label for="top-logprobs">Top Logprobs</Label>
            <Input
              id="top-logprobs"
              v-model.number="config.top_logprobs"
              type="number"
              min="1"
              max="10"
              placeholder="1"
            />
          </div>
        </div>
        <DialogFooter>
          <Button @click="showConfigModal = false">Done</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Response Panel -->
    <Card v-if="response" class="mt-8">
      <CardHeader>
        <CardTitle>Completion Response</CardTitle>
        <CardDescription>
          Completion result from {{ selectedNimId }}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div class="space-y-4">
          <!-- Request ID -->
          <div class="text-sm text-gray-600 dark:text-gray-400">
            Request ID: {{ response.id }}
          </div>

          <!-- Response Content -->
          <div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
            <TokenVisualization
              v-if="shouldShowTokenVisualization"
              :tokens="tokens"
            />
            <div v-else-if="responseContent" class="whitespace-pre-wrap text-sm">{{ responseContent }}</div>
            <div v-else class="text-sm text-gray-500 dark:text-gray-400 italic">
              No response content found. Check debug information below.
            </div>

            <!-- Fallback: Show raw response if no content found -->
            <div v-if="!responseContent && response" class="mt-4 p-3 bg-gray-100 dark:bg-gray-800 rounded border">
              <h5 class="text-sm font-medium mb-2">Raw Response Data:</h5>
              <pre class="text-xs overflow-auto max-h-60">{{ JSON.stringify(response, null, 2) }}</pre>
            </div>
          </div>

          <!-- Usage Stats -->
          <div v-if="response.usage" class="grid grid-cols-3 gap-4 text-sm">
            <div class="text-center">
              <div class="font-medium">Prompt Tokens</div>
              <div class="text-gray-600 dark:text-gray-400">
                {{ response.usage.prompt_tokens }}
              </div>
            </div>
            <div class="text-center">
              <div class="font-medium">Completion Tokens</div>
              <div class="text-gray-600 dark:text-gray-400">
                {{ response.usage.completion_tokens }}
              </div>
            </div>
            <div class="text-center">
              <div class="font-medium">Total Tokens</div>
              <div class="text-gray-600 dark:text-gray-400">
                {{ response.usage.total_tokens }}
              </div>
            </div>
          </div>

          <!-- Debug Information Cards -->
          <div v-if="response" class="mt-6">
            <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Debug Information</h4>
            <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              <!-- Logprobs Status -->
              <Card class="p-3">
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Logprobs</div>
                <Badge :variant="hasLogprobsData ? 'default' : 'secondary'" class="text-xs">
                  {{ hasLogprobsData ? 'Enabled' : 'Disabled' }}
                </Badge>
              </Card>

              <!-- Tokens Count -->
              <Card class="p-3">
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Tokens</div>
                <div class="text-sm font-medium">{{ tokens.length }}</div>
              </Card>

              <!-- Visualization Status -->
              <Card class="p-3">
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Visualization</div>
                <Badge :variant="shouldShowTokenVisualization ? 'default' : 'secondary'" class="text-xs">
                  {{ shouldShowTokenVisualization ? 'Showing' : 'Hidden' }}
                </Badge>
              </Card>

              <!-- Response Length -->
              <Card class="p-3">
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Content Length</div>
                <div class="text-sm font-medium">{{ responseContent.length }} chars</div>
              </Card>

              <!-- Streaming Info (only show if streaming) -->
              <Card v-if="config.stream" class="p-3">
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Streaming Chunks</div>
                <div class="text-sm font-medium">{{ streamingChunks.length }}</div>
              </Card>

              <!-- Logprobs in Chunks (only show if streaming) -->
              <Card v-if="config.stream" class="p-3">
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Chunk Logprobs</div>
                <Badge :variant="hasLogprobsInChunks(streamingChunks) ? 'default' : 'secondary'" class="text-xs">
                  {{ hasLogprobsInChunks(streamingChunks) ? 'Present' : 'Missing' }}
                </Badge>
              </Card>
            </div>

            <!-- Raw Response (Collapsible) -->
            <div class="mt-4">
              <Collapsible>
                <CollapsibleTrigger as-child>
                  <Button variant="outline" size="sm" class="w-full">
                    <Icon name="lucide:code" class="mr-2 h-4 w-4" />
                    <span>View Raw Response Data</span>
                    <Icon name="lucide:chevron-down" class="ml-auto h-4 w-4" />
                  </Button>
                </CollapsibleTrigger>
                <CollapsibleContent class="mt-2">
                  <Card class="p-4">
                    <pre class="text-xs overflow-auto max-h-60 bg-gray-50 dark:bg-gray-800 p-3 rounded">{{ JSON.stringify(response, null, 2) }}</pre>
                  </Card>
                </CollapsibleContent>
              </Collapsible>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import TokenVisualization from '@/components/TokenVisualization.vue'
import { parseLogprobsFromResponse, parseLogprobsFromStreamingChunks, hasLogprobs, hasLogprobsInChunks, extractTextFromTokens, type Token } from '@/composables/useLogprobs'

// Runtime config
const runtimeConfig = useRuntimeConfig()
const apiBase = runtimeConfig.public.apiBase

// Reactive state
const selectedNimId = ref('')
const nimIds = ref<string[]>([])
const isLoading = ref(false)
const isLoadingModels = ref(false)
const error = ref('')
const successMessage = ref('')
const response = ref<any>(null)
const showConfigModal = ref(false)
const tokens = ref<Token[]>([])
const streamingChunks = ref<any[]>([])

// Configuration
const config = ref({
  model: 'llama-3.1-8b-instruct',
  temperature: 0.7,
  max_tokens: 2048,
  stream: false,
  logprobs: false,
  top_logprobs: 1
})

// Prompt
const prompt = ref('')

// Computed properties
const canRunCompletion = computed(() => {
  return selectedNimId.value &&
         config.value.model &&
         prompt.value &&
         !isLoading.value
})

const responseContent = computed(() => {
  if (!response.value) return ''

  // Try different possible response structures
  if (response.value.choices?.[0]?.text) {
    return response.value.choices[0].text
  }

  // Fallback: if we have tokens, extract text from them
  if (tokens.value.length > 0) {
    return extractTextFromTokens(tokens.value)
  }

  // Another fallback: look for text in other possible locations
  if (response.value.text) {
    return response.value.text
  }

  // Check for message content (chat format)
  if (response.value.choices?.[0]?.message?.content) {
    return response.value.choices[0].message.content
  }

  // Check for delta content (streaming format)
  if (response.value.choices?.[0]?.delta?.text) {
    return response.value.choices[0].delta.text
  }

  // Last resort: try to extract any text from the response recursively
  const extractAnyText = (obj: any): string => {
    if (typeof obj === 'string') return obj
    if (typeof obj === 'number') return obj.toString()
    if (Array.isArray(obj)) {
      return obj.map(extractAnyText).join('')
    }
    if (obj && typeof obj === 'object') {
      return Object.values(obj).map(extractAnyText).join('')
    }
    return ''
  }

  const extractedText = extractAnyText(response.value)
  if (extractedText.trim()) {
    console.log('Extracted text from response:', extractedText)
    return extractedText
  }

  // Debug: log the actual response structure
  console.log('Response structure:', response.value)
  return ''
})

const hasLogprobsData = computed(() => {
  if (!response.value) return false

  // For streaming responses, check chunks for logprobs
  if (config.value.stream && streamingChunks.value.length > 0) {
    return hasLogprobsInChunks(streamingChunks.value)
  }

  // Check multiple possible logprobs structures
  const hasStandardLogprobs = hasLogprobs(response.value)
  if (hasStandardLogprobs) return true

  // Check for alternative logprobs structures
  if (response.value.choices?.[0]?.logprobs) return true
  if (response.value.logprobs) return true

  // Check for completion format with separate arrays
  const choice = response.value.choices?.[0]
  if (choice?.logprobs?.tokens && Array.isArray(choice.logprobs.tokens)) return true

  // Debug: log the response structure for logprobs
  console.log('Checking logprobs in response:', response.value)
  return false
})

const shouldShowTokenVisualization = computed(() => {
  return config.value.logprobs && hasLogprobsData.value && tokens.value.length > 0
})

// Methods
const loadNims = async () => {
  try {
    const res = await fetch(`${apiBase}/api/nims/`)
    if (!res.ok) throw new Error('Failed to load NIMs')
    const data = await res.json()
    const allNimIds = data.nim_ids || []

    // Load full configuration for each NIM and filter for LLM type
    const llmNimIds = []
    for (const nimId of allNimIds) {
      try {
        const nimRes = await fetch(`${apiBase}/api/nims/${encodeURIComponent(nimId)}`)
        if (nimRes.ok) {
          const nimConfig = await nimRes.json()
          if (nimConfig.nim_type === 'llm') {
            llmNimIds.push(nimId)
          }
        }
      } catch (err) {
        console.error(`Failed to load config for ${nimId}:`, err)
      }
    }

    nimIds.value = llmNimIds

    // Auto-select the first LLM NIM if available
    if (nimIds.value.length > 0 && nimIds.value[0]) {
      selectedNimId.value = nimIds.value[0]
      // Load models for the selected NIM
      loadModels(selectedNimId.value)
    }
  } catch (err) {
    error.value = `Failed to load NIMs: ${err}`
  }
}

const loadModels = async (nimId: string) => {
  if (!nimId) return

  isLoadingModels.value = true
  try {
    // Check if NVIDIA API is enabled
    const toggleResponse = await fetch(`${apiBase}/api/nvidia/toggle`)
    const toggleData = await toggleResponse.json()
    const useNvidiaApi = toggleData.enabled

    if (useNvidiaApi) {
      // When using NVIDIA API, we don't need to load models from a local NIM
      // The model name should be the NIM ID itself (e.g., "nvidia/llama-3.1-8b-instruct")
      config.value.model = nimId
    } else {
      // Get NIM data to find host and port for local NIM
      const nimRes = await fetch(`${apiBase}/api/nims/${encodeURIComponent(nimId)}`)
      if (!nimRes.ok) throw new Error('Failed to get NIM data')
      const nimData = await nimRes.json()

      // Get models from local NIM
      const modelsRes = await fetch(`http://${nimData.host}:${nimData.port}/v1/models`)
      if (!modelsRes.ok) throw new Error('Failed to load models from NIM')
      const modelsData = await modelsRes.json()

      // Auto-populate the first model
      if (modelsData.data && modelsData.data.length > 0) {
        config.value.model = modelsData.data[0].id
      }
    }
  } catch (err) {
    error.value = `Failed to load models: ${err}`
  } finally {
    isLoadingModels.value = false
  }
}

const onNimChange = (nimId: any) => {
  if (nimId && typeof nimId === 'string') {
    loadModels(nimId)
  }
}

const runCompletion = async () => {
  if (!canRunCompletion.value) return

  isLoading.value = true
  error.value = ''
  successMessage.value = ''
  response.value = null
  tokens.value = []
  streamingChunks.value = []

  try {
    // Build request body
    const requestBody = {
      model: config.value.model,
      prompt: prompt.value,
      temperature: config.value.temperature,
      max_tokens: config.value.max_tokens,
      stream: config.value.stream,
      logprobs: config.value.logprobs,
      top_logprobs: config.value.logprobs ? config.value.top_logprobs : undefined
    }

    // Make completion request
    const toggleResponse = await fetch(`${apiBase}/api/nvidia/toggle`)
    const toggleData = await toggleResponse.json()
    const useNvidiaApi = toggleData.enabled

    const res = await fetch(`${apiBase}/api/llm/completion?nim_id=${encodeURIComponent(selectedNimId.value)}&use_nvidia_api=${useNvidiaApi}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    })

    if (!res.ok) {
      const errorData = await res.json()
      throw new Error(errorData.detail || 'Completion request failed')
    }

    if (config.value.stream) {
      // Handle streaming response
      const reader = res.body?.getReader()
      const decoder = new TextDecoder()
      let streamedContent = ''

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const jsonStr = line.slice(6)
              if (jsonStr.trim() === '[DONE]') continue

              try {
                const data = JSON.parse(jsonStr)

                // Collect chunks for logprobs parsing
                streamingChunks.value.push(data)

                if (data.choices?.[0]?.text) {
                  streamedContent += data.choices[0].text

                  // Update response immediately for each token
                  response.value = {
                    id: data.id,
                    choices: [{
                      text: streamedContent
                    }]
                  }

                  // Parse logprobs from accumulated chunks if enabled
                  if (config.value.logprobs && hasLogprobsInChunks(streamingChunks.value)) {
                    try {
                      tokens.value = parseLogprobsFromStreamingChunks(streamingChunks.value)
                      console.log('Parsed streaming tokens:', tokens.value)
                    } catch (error) {
                      console.error('Failed to parse streaming logprobs:', error)
                    }
                  }

                  // Force UI update
                  await new Promise(resolve => setTimeout(resolve, 0))
                }
              } catch (e) {
                // Skip invalid JSON lines
              }
            }
          }
        }
      }
      successMessage.value = 'Streaming completion completed!'
    } else {
      // Handle non-streaming response
      const data = await res.json()
      response.value = data

      // Parse tokens if logprobs are enabled
      if (config.value.logprobs && hasLogprobsData.value) {
        try {
          tokens.value = parseLogprobsFromResponse(data)
          console.log('Parsed tokens:', tokens.value)
        } catch (error) {
          console.error('Failed to parse logprobs:', error)
          console.log('Response data for parsing:', data)
          tokens.value = []
        }
      } else {
        tokens.value = []
      }

      successMessage.value = 'Completion completed successfully!'
    }

  } catch (err) {
    error.value = `Completion failed: ${err}`
  } finally {
    isLoading.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadNims()
})
</script>
