<template>
  <div class="max-w-6xl">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold mb-2">Flux Schnell Image Generation</h1>
      <p class="text-muted-foreground">Generate high-quality images using FLUX.1-schnell model</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Left Side - Form -->
      <div class="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Generation Parameters</CardTitle>
            <CardDescription>
              Configure your image generation settings
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-6">
            <!-- View JSON Button -->
            <div class="flex justify-end">
              <Button
                variant="outline"
                @click="showJsonModal = true"
                class="flex items-center gap-2"
              >
                <Icon name="lucide:code" class="h-4 w-4" />
                View JSON
              </Button>
            </div>

            <!-- Prompt Input -->
            <div class="space-y-2">
              <Label for="prompt">Prompt</Label>
              <Textarea
                id="prompt"
                v-model="formData.prompt"
                placeholder="Enter your image generation prompt..."
                class="min-h-[100px]"
              />
            </div>

            <!-- Steps Input -->
            <div class="space-y-2">
              <Label for="steps">Steps</Label>
              <Input
                id="steps"
                v-model.number="formData.steps"
                type="number"
                min="1"
                max="50"
                placeholder="4"
              />
              <p class="text-sm text-muted-foreground">
                Number of denoising steps (default: 4)
              </p>
            </div>

            <!-- CFG Scale Input -->
            <div class="space-y-2">
              <Label for="cfg">CFG Scale</Label>
              <Input
                id="cfg"
                v-model.number="formData.cfg_scale"
                type="number"
                min="0"
                max="20"
                step="0.1"
                placeholder="0"
              />
              <p class="text-sm text-muted-foreground">
                Classifier-free guidance scale (default: 0)
              </p>
            </div>

            <!-- Additional Parameters -->
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-2">
                <Label for="width">Width</Label>
                <Select v-model="formData.width">
                  <SelectTrigger>
                    <SelectValue placeholder="Select width" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem :value="512">512px</SelectItem>
                    <SelectItem :value="768">768px</SelectItem>
                    <SelectItem :value="1024">1024px</SelectItem>
                    <SelectItem :value="1536">1536px</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div class="space-y-2">
                <Label for="height">Height</Label>
                <Select v-model="formData.height">
                  <SelectTrigger>
                    <SelectValue placeholder="Select height" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem :value="512">512px</SelectItem>
                    <SelectItem :value="768">768px</SelectItem>
                    <SelectItem :value="1024">1024px</SelectItem>
                    <SelectItem :value="1536">1536px</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <!-- Generate Button -->
            <Button
              @click="generateImage"
              :disabled="loading || !formData.prompt.trim()"
              class="w-full"
              size="lg"
            >
              <Icon v-if="loading" name="lucide:loader-2" class="h-4 w-4 mr-2 animate-spin" />
              <Icon v-else name="lucide:sparkles" class="h-4 w-4 mr-2" />
              {{ loading ? 'Generating...' : 'Generate Image' }}
            </Button>
          </CardContent>
        </Card>
      </div>

      <!-- Right Side - Results -->
      <div class="space-y-6">
        <!-- Generated Image -->
        <Card>
          <CardHeader>
            <CardTitle>Generated Image</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="space-y-4">
              <div class="relative">
                <!-- Generated Image -->
                <img
                  v-if="generatedImage"
                  :src="generatedImage"
                  :alt="formData.prompt"
                  class="w-full rounded-lg border"
                />
                <!-- Placeholder -->
                <div
                  v-else
                  class="w-full h-64 bg-muted rounded-lg border-2 border-dashed border-muted-foreground/25 flex items-center justify-center"
                >
                  <div class="text-center text-muted-foreground">
                    <Icon name="lucide:image" class="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p class="text-sm">Generated image will appear here</p>
                  </div>
                </div>
                <Button
                  v-if="generatedImage"
                  @click="downloadImage"
                  variant="outline"
                  size="sm"
                  class="absolute top-2 right-2"
                >
                  <Icon name="lucide:download" class="h-4 w-4 mr-2" />
                  Download
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Content Filtered Message -->
        <Card v-if="contentFiltered">
          <CardHeader>
            <CardTitle class="text-amber-600">Request Successful - Content Filtered</CardTitle>
          </CardHeader>
          <CardContent>
            <div>
              <p class="text-amber-600 font-medium">Request completed successfully</p>
              <p class="text-sm text-muted-foreground mt-1">
                The image generation was blocked by content filters. The prompt may contain content that violates safety guidelines. Please try a different prompt.
              </p>
            </div>
          </CardContent>
        </Card>

        <!-- Metadata -->
        <Card v-if="inferenceResult">
          <CardHeader>
            <CardTitle>Generation Metadata</CardTitle>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span class="font-medium text-muted-foreground">Request ID:</span>
                <p class="font-mono text-xs break-all">{{ inferenceResult.request_id }}</p>
              </div>
              <div>
                <span class="font-medium text-muted-foreground">Status:</span>
                <Badge :variant="inferenceResult.status === 'completed' ? 'default' : 'destructive'">
                  {{ inferenceResult.status }}
                </Badge>
              </div>
              <div>
                <span class="font-medium text-muted-foreground">Created:</span>
                <p>{{ formatDate(inferenceResult.date_created) }}</p>
              </div>
              <div>
                <span class="font-medium text-muted-foreground">Updated:</span>
                <p>{{ formatDate(inferenceResult.date_updated) }}</p>
              </div>
            </div>

            <!-- Output Details -->
            <div v-if="inferenceResult.output" class="space-y-2">
              <h4 class="font-medium">Output Details</h4>
              <div class="bg-muted p-3 rounded-lg">
                <pre class="text-xs overflow-auto">{{ JSON.stringify(inferenceResult.output, null, 2) }}</pre>
              </div>
            </div>

            <!-- Error Details -->
            <div v-if="inferenceResult.error" class="space-y-2">
              <h4 class="font-medium text-destructive">Error Details</h4>
              <div class="bg-destructive/10 p-3 rounded-lg">
                <pre class="text-xs text-destructive overflow-auto">{{ JSON.stringify(inferenceResult.error, null, 2) }}</pre>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Error State -->
        <Card v-if="error">
          <CardHeader>
            <CardTitle class="text-destructive">Generation Failed</CardTitle>
          </CardHeader>
          <CardContent>
            <p class="text-destructive">{{ error }}</p>
          </CardContent>
        </Card>
      </div>
    </div>

    <!-- JSON Modal -->
    <Dialog v-model:open="showJsonModal">
      <DialogContent class="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Request JSON Payload</DialogTitle>
          <DialogDescription>
            This is the JSON payload that will be sent to the API
          </DialogDescription>
        </DialogHeader>
        <div class="space-y-4">
          <div class="bg-muted p-4 rounded-lg">
            <pre class="text-sm overflow-auto">{{ JSON.stringify(getPayloadForDisplay(), null, 2) }}</pre>
          </div>
          <div class="flex justify-end">
            <Button @click="showJsonModal = false" variant="outline">
              Close
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
interface FormData {
  prompt: string
  steps: number
  cfg_scale: number
  height: number
  width: number
  mode: string
  image: string | null
  samples: number
  seed: number
}

interface InferenceResult {
  request_id: string
  nim_id: string
  type: string
  request_type: string
  model: string
  status: string
  date_created: string
  date_updated: string
  input: FormData
  output?: any
  error?: any
  nim_metadata: any
  nim_config: any
}

const config = useRuntimeConfig()
const route = useRoute()

// Form data
const formData = ref<FormData>({
  prompt: '',
  steps: 4,
  cfg_scale: 0,
  height: 1024,
  width: 1024,
  mode: 'base',
  image: null,
  samples: 1,
  seed: 0
})

// State
const loading = ref(false)
const error = ref<string | null>(null)
const generatedImage = ref<string | null>(null)
const inferenceResult = ref<InferenceResult | null>(null)
const showJsonModal = ref(false)
const contentFiltered = ref(false)

// Extract NIM ID from route
const nimId = computed(() => {
  const provider = route.params.provider as string
  const name = route.params.name as string
  return `${provider}/${name}`
})

const getPayloadForDisplay = () => {
  return formData.value
}

const generateImage = async () => {
  if (!formData.value.prompt.trim()) {
    error.value = 'Please enter a prompt'
    return
  }

  try {
    loading.value = true
    error.value = null
    generatedImage.value = null
    inferenceResult.value = null
    contentFiltered.value = false

    console.log('Generating image with data:', formData.value)

    const response = await $fetch<InferenceResult>(`${config.public.apiBase}/v0/nims/${nimId.value}`, {
      method: 'POST',
      body: formData.value
    })

    console.log('Generation response:', response)
    inferenceResult.value = response

    // Extract image from response
    if (response.output && response.output.artifacts && response.output.artifacts.length > 0) {
      const artifact = response.output.artifacts[0]
      if (artifact.finishReason === "CONTENT_FILTERED") {
        // Handle content filtered case - this is a successful request
        generatedImage.value = null
        contentFiltered.value = true
        error.value = null // Clear any previous errors
      } else if (artifact.base64) {
        generatedImage.value = `data:image/jpeg;base64,${artifact.base64}`
        contentFiltered.value = false
      }
    }

  } catch (err: any) {
    console.error('Image generation failed:', err)
    error.value = err.data?.detail || err.message || 'Image generation failed'
  } finally {
    loading.value = false
  }
}

const downloadImage = () => {
  if (!generatedImage.value) return

  const link = document.createElement('a')
  link.href = generatedImage.value
  link.download = `flux-schnell-${Date.now()}.jpg`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const formatDate = (dateString: string) => {
  try {
    return new Date(dateString).toLocaleString()
  } catch {
    return dateString
  }
}

// Set page metadata
useHead({
  title: 'Flux Schnell Generation - NIM Kit',
  meta: [
    { name: 'description', content: 'Generate high-quality images using FLUX.1-schnell model' }
  ]
})
</script>
