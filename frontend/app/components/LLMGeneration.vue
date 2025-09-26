<template>
  <div>
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold mb-2">LLM Inference</h1>
      <p class="text-muted-foreground">
        Generate text completions and chat responses using LLM models
      </p>
    </div>

    <!-- Configuration Prompt -->
    <div v-if="!isNimConfigured" class="mb-8">
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <Icon name="lucide:settings" class="h-5 w-5" />
            NIM Configuration Required
          </CardTitle>
          <CardDescription>
            This LLM NIM needs to be configured before you can use it. You can either configure it locally or use the NVIDIA API.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div class="space-y-4">
            <div class="p-4 bg-muted rounded-lg">
              <h4 class="font-medium mb-2">Option 1: Use NVIDIA API (Recommended)</h4>
              <p class="text-sm text-muted-foreground mb-3">
                Enable NVIDIA API to use this NIM without local configuration. This is the easiest way to get started.
                <NuxtLink to="/nvidia-config" class="text-primary hover:underline ml-1">
                  Configure API key first
                </NuxtLink>
              </p>
              <Button @click="enableNvidiaApi" class="w-full">
                <Icon name="lucide:zap" class="mr-2 h-4 w-4" />
                Enable NVIDIA API
              </Button>
            </div>

            <div class="p-4 bg-muted rounded-lg">
              <h4 class="font-medium mb-2">Option 2: Configure Local NIM</h4>
              <p class="text-sm text-muted-foreground mb-3">
                If you have this NIM running locally, configure the connection details.
              </p>
              <Button variant="outline" @click="showConfigForm = true" class="w-full">
                <Icon name="lucide:server" class="mr-2 h-4 w-4" />
                Configure Local NIM
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Left Side - Form -->
      <div class="space-y-6">
        <Card>
          <CardHeader>
            <div class="flex justify-between items-start">
              <div>
                <CardTitle>Generation Parameters</CardTitle>
                <CardDescription>
                  Configure your LLM inference settings
                </CardDescription>
              </div>
              <Button
                variant="outline"
                @click="showConfigModal = true"
                class="flex items-center gap-2"
              >
                <Icon name="lucide:settings" class="h-4 w-4" />
                Advanced Config
              </Button>
            </div>
          </CardHeader>
          <CardContent class="space-y-6">
            <!-- Mode Toggle -->
            <div class="space-y-2">
              <Label>Mode</Label>
              <div class="flex items-center space-x-4">
                <div class="flex items-center space-x-2">
                  <input
                    id="chat-mode"
                    v-model="mode"
                    type="radio"
                    value="chat"
                    class="h-4 w-4 text-primary"
                    @click="refreshNvidiaApiStatus"
                  />
                  <Label for="chat-mode" class="cursor-pointer">Chat</Label>
                </div>
                <div v-if="!isNvidiaApiEnabled" class="flex items-center space-x-2">
                  <input
                    id="completion-mode"
                    v-model="mode"
                    type="radio"
                    value="completion"
                    class="h-4 w-4 text-primary"
                    @click="refreshNvidiaApiStatus"
                  />
                  <Label for="completion-mode" class="cursor-pointer">Completion</Label>
                </div>
              </div>
              <p class="text-sm text-muted-foreground">
                <span v-if="isNvidiaApiEnabled">
                  Chat mode is available with NVIDIA API
                </span>
                <span v-else>
                  Choose between chat (conversational) or completion (text generation) mode
                </span>
              </p>
            </div>

            <!-- System Prompt (Chat mode only) -->
            <div v-if="mode === 'chat'" class="space-y-2">
              <Label for="system-prompt">System Prompt</Label>
              <Textarea
                id="system-prompt"
                v-model="systemPrompt"
                placeholder="You are a helpful assistant..."
                rows="3"
              />
            </div>

            <!-- User Input -->
            <div class="space-y-2">
              <Label for="user-input">
                {{ mode === 'chat' ? 'Your Message' : 'Prompt' }}
              </Label>
              <Textarea
                id="user-input"
                v-model="userInput"
                :placeholder="mode === 'chat' ? 'Enter your message here... (⌘+Enter to send)' : 'Enter your prompt here... (⌘+Enter to send)'"
                rows="8"
                @keydown="handleKeydown"
              />
            </div>

            <!-- Submit Button -->
            <Button
              @click="runInference"
              :disabled="!canRunInference || isLoading"
              class="w-full"
              size="lg"
            >
              <Icon name="lucide:loader-2" v-if="isLoading" class="mr-2 h-4 w-4 animate-spin" />
              {{ isLoading ? 'Running Inference...' : (mode === 'chat' ? 'Send Message' : 'Generate Completion') }}
              <span v-if="!isLoading" class="ml-2 text-xs opacity-70">⌘+Enter</span>
            </Button>
          </CardContent>
        </Card>

        <!-- Configuration Modal -->
        <Dialog v-model:open="showConfigModal">
          <DialogContent class="max-w-md">
            <DialogHeader>
              <DialogTitle>Advanced Configuration</DialogTitle>
              <DialogDescription>
                Configure advanced LLM inference parameters
              </DialogDescription>
            </DialogHeader>
            <div class="space-y-6">
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

        <!-- Local NIM Configuration Modal -->
        <Dialog v-model:open="showConfigForm">
          <DialogContent class="max-w-md">
            <DialogHeader>
              <DialogTitle>Configure Local NIM</DialogTitle>
              <DialogDescription>
                Enter the connection details for your local NIM instance
              </DialogDescription>
            </DialogHeader>
            <div class="space-y-6">
              <!-- Host Input -->
              <div class="space-y-2">
                <Label for="config-host">Host</Label>
                <Input
                  id="config-host"
                  v-model="localConfig.host"
                  placeholder="localhost"
                />
              </div>

              <!-- Port Input -->
              <div class="space-y-2">
                <Label for="config-port">Port</Label>
                <Input
                  id="config-port"
                  v-model.number="localConfig.port"
                  type="number"
                  placeholder="8000"
                />
              </div>

              <!-- NIM Type -->
              <div class="space-y-2">
                <Label for="config-type">NIM Type</Label>
                <Input
                  id="config-type"
                  v-model="localConfig.nim_type"
                  value="llm"
                  disabled
                />
                <p class="text-sm text-muted-foreground">
                  This NIM type is automatically set to 'llm'
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" @click="showConfigForm = false">Cancel</Button>
              <Button @click="configureLocalNim" :disabled="!localConfig.host || !localConfig.port">
                Configure NIM
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <!-- Right Side - Results -->
      <div class="space-y-6">
        <!-- Error Alert -->
        <Alert v-if="error" variant="destructive">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{{ error }}</AlertDescription>
        </Alert>

        <!-- Response Panel -->
        <Card v-if="response || isLoading" class="h-[600px] flex flex-col">
          <CardHeader>
            <div class="flex items-center gap-2">
              <CardTitle>Response</CardTitle>
              <Badge v-if="successMessage && !isLoading" variant="default" class="bg-green-100 text-green-800 border-green-200 dark:bg-green-900/20 dark:text-green-200 dark:border-green-800">
                Success
              </Badge>
            </div>
            <CardDescription>
              {{ isLoading ? 'Generating response...' : `Inference result from ${nimId}` }}
            </CardDescription>
          </CardHeader>
          <CardContent class="flex-1 flex flex-col min-h-0">
            <div class="flex-1 overflow-hidden">
              <!-- Response Content -->
              <div
                ref="responseContainer"
                class="bg-muted rounded-lg p-4 h-full overflow-y-auto pb-6"
              >
                <TokenVisualization
                  v-if="shouldShowTokenVisualization"
                  :tokens="tokens"
                  class="pb-4"
                />
                <pre v-else class="whitespace-pre-wrap text-sm pb-4">{{ responseContent }}</pre>

                <!-- Loading indicator for streaming -->
                <div v-if="isLoading && config.stream" class="flex items-center space-x-2 mt-4">
                  <Icon name="lucide:loader-2" class="h-4 w-4 animate-spin" />
                  <span class="text-sm text-muted-foreground">Streaming...</span>
                </div>
              </div>

              <!-- Usage Stats -->
              <div v-if="response?.usage" class="grid grid-cols-3 gap-4 text-sm mt-4">
                <div class="text-center">
                  <div class="font-medium">Prompt Tokens</div>
                  <div class="text-muted-foreground">
                    {{ response.usage.prompt_tokens }}
                  </div>
                </div>
                <div class="text-center">
                  <div class="font-medium">Completion Tokens</div>
                  <div class="text-muted-foreground">
                    {{ response.usage.completion_tokens }}
                  </div>
                </div>
                <div class="text-center">
                  <div class="font-medium">Total Tokens</div>
                  <div class="text-muted-foreground">
                    {{ response.usage.total_tokens }}
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Empty State -->
        <Card v-else class="h-[600px] flex items-center justify-center">
          <div class="text-center text-muted-foreground">
            <Icon name="lucide:message-square" class="h-12 w-12 mx-auto mb-4" />
            <h3 class="text-lg font-medium mb-2">No Response Yet</h3>
            <p>Run an inference to see results here</p>
          </div>
        </Card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import TokenVisualization from '@/components/TokenVisualization.vue'
import { parseLogprobsFromResponse, parseLogprobsFromStreamingChunks, hasLogprobs, hasLogprobsInChunks, extractTextFromTokens, type Token } from '@/composables/useLogprobs'

// Props
interface Props {
  nimId: string
}

const props = defineProps<Props>()

// Check if NIM is configured
const nimConfig = ref<{host: string, port: number, nim_type?: string} | null>(null)
const isNimConfigured = computed(() => !!nimConfig.value)

// Runtime config
const runtimeConfig = useRuntimeConfig()
const apiBase = runtimeConfig.public.apiBase

// Reactive state
const isLoading = ref(false)
const isLoadingModels = ref(false)
const error = ref('')
const successMessage = ref('')
const response = ref<any>(null)
const showConfigModal = ref(false)
const showConfigForm = ref(false)
const tokens = ref<Token[]>([])
const streamingChunks = ref<any[]>([])
const responseContainer = ref<HTMLElement>()

// Local configuration
const localConfig = ref({
  host: 'localhost',
  port: 8000,
  nim_type: 'llm'
})

// Mode and input
const mode = ref<'chat' | 'completion'>('chat')
const systemPrompt = ref('You are a helpful assistant.')
const userInput = ref('')

// Configuration
const config = ref({
  model: 'llama-3.1-8b-instruct',
  temperature: 0.7,
  max_tokens: 2048,
  stream: false,
  logprobs: false,
  top_logprobs: 1
})

// Computed properties
const canRunInference = computed(() => {
  return props.nimId &&
         config.value.model &&
         userInput.value &&
         !isLoading.value
})

const isNvidiaApiEnabled = ref(false)

const responseContent = computed(() => {
  if (!response.value) return ''

  if (mode.value === 'chat') {
    return response.value?.choices?.[0]?.message?.content || ''
  } else {
    return response.value?.choices?.[0]?.text || ''
  }
})

const hasLogprobsData = computed(() => {
  if (!response.value) return false

  // For streaming responses, check chunks for logprobs
  if (config.value.stream && streamingChunks.value.length > 0) {
    return hasLogprobsInChunks(streamingChunks.value)
  }

  return hasLogprobs(response.value)
})

const shouldShowTokenVisualization = computed(() => {
  return config.value.logprobs && hasLogprobsData.value && tokens.value.length > 0
})

// Methods
const fetchNimConfig = async () => {
  try {
    const response = await fetch(`${apiBase}/api/nims/config/${encodeURIComponent(props.nimId)}`)
    if (response.ok) {
      const config = await response.json()
      nimConfig.value = config
    }
  } catch (err) {
    console.error('Failed to fetch NIM config:', err)
  }
}

const refreshNvidiaApiStatus = async () => {
  try {
    console.log('Checking NVIDIA API status at:', `${apiBase}/api/nvidia/toggle`)
    const toggleResponse = await fetch(`${apiBase}/api/nvidia/toggle`)
    console.log('NVIDIA API toggle response status:', toggleResponse.status)

    if (!toggleResponse.ok) {
      console.warn('NVIDIA API toggle endpoint not available, assuming disabled')
      isNvidiaApiEnabled.value = false
      return
    }
    const toggleData = await toggleResponse.json()
    console.log('NVIDIA API toggle data:', toggleData)
    isNvidiaApiEnabled.value = toggleData.enabled

    // If NVIDIA API is disabled, allow both modes
    if (!toggleData.enabled) {
      // Don't force mode, let user choose
    }
  } catch (err) {
    console.error('Failed to fetch NVIDIA API status:', err)
    // Default to disabled if we can't fetch the status
    isNvidiaApiEnabled.value = false
  }
}

const loadModels = async () => {
  if (!props.nimId) return

  isLoadingModels.value = true
  try {
    // Check if NVIDIA API is enabled (optional - don't fail if this doesn't work)
    try {
      await refreshNvidiaApiStatus()
    } catch (err) {
      console.warn('Could not check NVIDIA API status, assuming disabled:', err)
      isNvidiaApiEnabled.value = false
    }
    const useNvidiaApi = isNvidiaApiEnabled.value

    if (useNvidiaApi) {
      // When using NVIDIA API, we don't need to load models from a local NIM
      // The model name should be the NIM ID itself (e.g., "nvidia/llama-3.1-8b-instruct")
      config.value.model = props.nimId
      // Force chat mode since NVIDIA API doesn't support completions
      mode.value = 'chat'
    } else {
      // Get NIM data to find host and port for local NIM
      const nimRes = await fetch(`${apiBase}/api/nims/${encodeURIComponent(props.nimId)}`)
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

const scrollToBottom = async () => {
  await nextTick()
  if (responseContainer.value) {
    responseContainer.value.scrollTop = responseContainer.value.scrollHeight
  }
}

const runInference = async () => {
  if (!canRunInference.value) return

  isLoading.value = true
  error.value = ''
  successMessage.value = ''
  response.value = null
  tokens.value = []
  streamingChunks.value = []

  try {
    let requestBody: any
    let endpoint: string

    if (mode.value === 'chat') {
      // Build messages array for chat
      const messages = []
      if (systemPrompt.value) {
        messages.push({
          role: 'system',
          content: systemPrompt.value
        })
      }
      messages.push({
        role: 'user',
        content: userInput.value
      })

      requestBody = {
        model: config.value.model,
        messages,
        temperature: config.value.temperature,
        max_tokens: config.value.max_tokens,
        stream: config.value.stream,
        logprobs: config.value.logprobs,
        top_logprobs: config.value.logprobs ? config.value.top_logprobs : undefined
      }

      endpoint = `${apiBase}/api/llm/inference?nim_id=${encodeURIComponent(props.nimId)}&use_nvidia_api=${await getNvidiaApiToggle()}`
    } else {
      // Build request body for completion
      requestBody = {
        model: config.value.model,
        prompt: userInput.value,
        temperature: config.value.temperature,
        max_tokens: config.value.max_tokens,
        stream: config.value.stream,
        logprobs: config.value.logprobs,
        top_logprobs: config.value.logprobs ? config.value.top_logprobs : undefined
      }

      endpoint = `${apiBase}/api/llm/completion?nim_id=${encodeURIComponent(props.nimId)}&use_nvidia_api=${await getNvidiaApiToggle()}`
    }

    const res = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    })

    if (!res.ok) {
      const errorData = await res.json()
      throw new Error(errorData.detail || 'Inference request failed')
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

                let content = ''
                if (mode.value === 'chat') {
                  content = data.choices?.[0]?.delta?.content || ''
                } else {
                  content = data.choices?.[0]?.text || ''
                }

                if (content) {
                  streamedContent += content

                  // Update response immediately for each token
                  if (mode.value === 'chat') {
                    response.value = {
                      id: data.id,
                      choices: [{
                        message: {
                          role: 'assistant',
                          content: streamedContent
                        }
                      }]
                    }
                  } else {
                    response.value = {
                      id: data.id,
                      choices: [{
                        text: streamedContent
                      }]
                    }
                  }

                  // Parse logprobs from accumulated chunks if enabled
                  if (config.value.logprobs && hasLogprobsInChunks(streamingChunks.value)) {
                    try {
                      tokens.value = parseLogprobsFromStreamingChunks(streamingChunks.value)
                    } catch (error) {
                      console.error('Failed to parse streaming logprobs:', error)
                    }
                  }

                  // Scroll to bottom for streaming
                  await scrollToBottom()

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

      successMessage.value = 'Streaming inference completed!'
    } else {
      // Handle non-streaming response
      console.log('Processing non-streaming response...')
      const data = await res.json()
      console.log('Received non-streaming data:', data)
      response.value = data

      // Parse tokens if logprobs are enabled
      if (config.value.logprobs && hasLogprobs(data)) {
        tokens.value = parseLogprobsFromResponse(data)
      } else {
        tokens.value = []
      }

      successMessage.value = 'Inference completed successfully!'
      console.log('Non-streaming inference completed')
    }

  } catch (err) {
    error.value = `Inference failed: ${err}`
  } finally {
    isLoading.value = false
  }
}

const getNvidiaApiToggle = async (): Promise<boolean> => {
  const toggleResponse = await fetch(`${apiBase}/api/nvidia/toggle`)
  const toggleData = await toggleResponse.json()
  return toggleData.enabled
}

const enableNvidiaApi = async () => {
  try {
    const response = await fetch(`${apiBase}/api/nvidia/toggle`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ enabled: true })
    })

    if (response.ok) {
      successMessage.value = 'NVIDIA API enabled successfully! You can now use this NIM.'
      isNvidiaApiEnabled.value = true
      // Force chat mode since NVIDIA API doesn't support completions
      mode.value = 'chat'
      // Refresh the config to see if it's now available
      await fetchNimConfig()
      if (isNimConfigured.value) {
        await loadModels()
      }
    } else {
      const errorData = await response.json()
      if (errorData.detail?.includes('API key')) {
        error.value = 'NVIDIA API key is required. Please configure your API key first in the NVIDIA settings.'
      } else {
        error.value = errorData.detail || 'Failed to enable NVIDIA API'
      }
    }
  } catch (err) {
    error.value = `Failed to enable NVIDIA API: ${err}`
  }
}

const configureLocalNim = async () => {
  try {
    const response = await fetch(`${apiBase}/api/nims/${encodeURIComponent(props.nimId)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        host: localConfig.value.host,
        port: localConfig.value.port,
        nim_type: localConfig.value.nim_type
      })
    })

    if (response.ok) {
      successMessage.value = `Successfully configured ${props.nimId} at ${localConfig.value.host}:${localConfig.value.port}`
      showConfigForm.value = false
      // Refresh the config
      await fetchNimConfig()
      if (isNimConfigured.value) {
        await loadModels()
      }
    } else {
      const errorData = await response.json()
      error.value = errorData.detail || 'Failed to configure NIM'
    }
  } catch (err) {
    error.value = `Failed to configure NIM: ${err}`
  }
}

const handleKeydown = (event: KeyboardEvent) => {
  // Check for Command+Enter (Mac) or Ctrl+Enter (Windows/Linux)
  if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
    event.preventDefault()
    if (canRunInference.value && !isLoading.value) {
      runInference()
    }
  }
}

// Watch for mode changes to clear response
watch(mode, () => {
  response.value = null
  error.value = ''
  successMessage.value = ''
})

// Lifecycle
onMounted(async () => {
  try {
    await refreshNvidiaApiStatus()
  } catch (err) {
    console.warn('Could not check NVIDIA API status on mount:', err)
    isNvidiaApiEnabled.value = false
  }

  await fetchNimConfig()
  if (isNimConfigured.value) {
    await loadModels()
  }
})
</script>
