<template>
  <div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Left Side - Form -->
      <div class="space-y-6">
        <Card>
          <CardHeader>
            <div class="flex justify-between items-start">
              <div>
                <CardTitle>Image Input</CardTitle>
                <CardDescription>
                  Upload an image file to extract text with bounding boxes
                </CardDescription>
              </div>
              <Button
                variant="outline"
                @click="showJsonModal = true"
                class="flex items-center gap-2"
              >
                <Icon name="lucide:code" class="h-4 w-4" />
                View JSON
              </Button>
            </div>
          </CardHeader>
          <CardContent class="space-y-6">
            <!-- File Upload Section -->
            <div class="space-y-4">
              <div class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <input
                  ref="fileInput"
                  type="file"
                  accept="image/*"
                  @change="handleFileUpload"
                  class="hidden"
                />
                <div v-if="!uploadedFile" class="space-y-2">
                  <Icon name="lucide:upload" class="h-8 w-8 mx-auto text-gray-400" />
                  <p class="text-sm text-gray-600">Click to upload image file</p>
                  <Button @click="$refs.fileInput.click()" variant="outline">
                    Choose File
                  </Button>
                </div>
                <div v-else class="space-y-2">
                  <Icon name="lucide:file-image" class="h-8 w-8 mx-auto text-green-500" />
                  <p class="text-sm font-medium">{{ uploadedFile.name }}</p>
                  <p class="text-xs text-gray-500">{{ formatFileSize(uploadedFile.size) }}</p>
                  <div class="flex gap-2 justify-center">
                    <Button @click="clearUploadedFile" variant="outline" size="sm">
                      Remove File
                    </Button>
                    <Button @click="previewImage" variant="outline" size="sm">
                      Preview
                    </Button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Image Preview -->
            <div v-if="imagePreview" class="space-y-2">
              <Label>Image Preview</Label>
              <div class="border rounded-lg p-4">
                <img
                  :src="imagePreview"
                  alt="Preview"
                  class="max-w-full h-auto max-h-64 mx-auto rounded"
                />
              </div>
            </div>

            <!-- NIM Selection -->
            <div v-if="!props.nimId" class="space-y-2">
              <Label for="nimId">PaddleOCR NIM</Label>
              <Select v-model="selectedNimId">
                <SelectTrigger>
                  <SelectValue placeholder="Select PaddleOCR NIM" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem
                    v-for="nim in paddleocrNims"
                    :key="nim.nim_id"
                    :value="nim.nim_id"
                  >
                    {{ nim.nim_id }}
                  </SelectItem>
                </SelectContent>
              </Select>
              <p class="text-sm text-muted-foreground">
                Select the PaddleOCR NIM instance to use for text detection
              </p>
            </div>

            <!-- API Toggle -->
            <div class="space-y-2">
              <Label>API Source</Label>
              <div class="flex gap-2">
                <Button
                  :variant="!useNvidiaApi ? 'default' : 'outline'"
                  @click="useNvidiaApi = false"
                  class="flex items-center gap-2"
                >
                  <Icon name="lucide:server" class="h-4 w-4" />
                  Local NIM
                </Button>
                <Button
                  :variant="useNvidiaApi ? 'default' : 'outline'"
                  @click="useNvidiaApi = true"
                  class="flex items-center gap-2"
                >
                  <Icon name="lucide:cloud" class="h-4 w-4" />
                  NVIDIA API
                </Button>
              </div>
              <p class="text-sm text-muted-foreground">
                Choose between local NIM or NVIDIA API
              </p>
            </div>

            <!-- Generate Button -->
            <Button
              @click="generateText"
              :disabled="!canGenerate"
              class="w-full"
              size="lg"
            >
              <Icon
                v-if="isGenerating"
                name="lucide:loader-2"
                class="h-4 w-4 mr-2 animate-spin"
              />
              <Icon
                v-else
                name="lucide:search"
                class="h-4 w-4 mr-2"
              />
              {{ isGenerating ? 'Detecting Text...' : 'Detect Text' }}
            </Button>
          </CardContent>
        </Card>
      </div>

      <!-- Right Side - Results -->
      <div class="space-y-6">
        <!-- Results Card -->
        <Card v-if="result">
          <CardHeader>
            <div class="flex justify-between items-start">
              <div>
                <CardTitle>Detection Results</CardTitle>
                <CardDescription>
                  Text detection results with confidence scores
                </CardDescription>
              </div>
              <div class="flex gap-2">
                <Button
                  v-if="result.visualization_path"
                  variant="outline"
                  size="sm"
                  @click="showVisualization = true"
                >
                  <Icon name="lucide:eye" class="h-4 w-4 mr-2" />
                  View Visualization
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  @click="copyResults"
                >
                  <Icon name="lucide:copy" class="h-4 w-4 mr-2" />
                  Copy Results
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <!-- Visualization Image at Top -->
            <div v-if="result.visualization_path" class="mb-6">
              <img
                :src="getVisualizationUrl(result.visualization_path)"
                alt="Text Detection Visualization"
                class="max-w-full h-auto rounded-lg border"
              />
              <p class="text-sm text-muted-foreground mt-2">
                Blue boxes show detected text regions with confidence scores
              </p>
            </div>

            <!-- Text Detections -->
            <div v-if="result.data && result.data.length > 0" class="space-y-4">
              <Accordion type="single" collapsible class="w-full">
                <AccordionItem
                  v-for="(detection, index) in result.data"
                  :key="index"
                  :value="`image-${index}`"
                  class="border rounded-lg"
                >
                  <AccordionTrigger class="px-4 py-3 hover:no-underline">
                    <div class="flex items-center justify-between w-full pr-4">
                      <span class="font-medium">Image {{ index + 1 }}</span>
                      <Badge variant="secondary" class="ml-2">
                        {{ detection.text_detections.length }} text regions
                      </Badge>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent class="px-4 pb-4">
                    <div class="space-y-2">
                      <div
                        v-for="(textDetection, textIndex) in detection.text_detections"
                        :key="textIndex"
                        class="flex justify-between items-start p-3 bg-muted rounded-lg"
                      >
                        <div class="flex-1">
                          <p class="font-medium text-foreground">{{ textDetection.text_prediction.text }}</p>
                          <p class="text-sm text-muted-foreground">
                            Confidence: {{ (textDetection.text_prediction.confidence * 100).toFixed(1) }}%
                          </p>
                        </div>
                        <Badge variant="outline" class="ml-2">
                          {{ textDetection.bounding_box.points.length }} corners
                        </Badge>
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </div>
            <div v-else class="text-center py-8 text-muted-foreground">
              <Icon name="lucide:file-x" class="h-8 w-8 mx-auto mb-2" />
              <p>No text detected in the image</p>
            </div>

            <!-- Complete JSON Results Accordion -->
            <div v-if="result" class="mt-6">
              <Accordion type="single" collapsible class="w-full">
                <AccordionItem value="json-results" class="border rounded-lg">
                  <AccordionTrigger class="px-4 py-3 hover:no-underline">
                    <span class="font-medium">Complete JSON Results</span>
                  </AccordionTrigger>
                  <AccordionContent class="px-4 pb-4">
                    <pre class="bg-muted p-4 rounded-lg text-sm overflow-auto max-h-96 text-foreground">{{ JSON.stringify(result, null, 2) }}</pre>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </div>
          </CardContent>
        </Card>

        <!-- Error Card -->
        <Card v-if="error" class="border-red-200">
          <CardHeader>
            <CardTitle class="text-red-600">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p class="text-red-600">{{ error }}</p>
          </CardContent>
        </Card>

        <!-- Loading Card -->
        <Card v-if="isGenerating">
          <CardContent class="py-8">
            <div class="text-center">
              <Icon name="lucide:loader-2" class="h-8 w-8 mx-auto mb-4 animate-spin" />
              <p>Detecting text in image...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>

    <!-- JSON Modal -->
    <Dialog v-model:open="showJsonModal">
      <DialogContent class="max-w-4xl">
        <DialogHeader>
          <DialogTitle>Request/Response JSON</DialogTitle>
        </DialogHeader>
        <div class="space-y-4">
          <div>
            <h4 class="font-medium mb-2">Request</h4>
            <pre class="bg-muted p-4 rounded-lg text-sm overflow-auto max-h-64 text-foreground">{{ JSON.stringify(requestData, null, 2) }}</pre>
          </div>
          <div v-if="result">
            <h4 class="font-medium mb-2">Response</h4>
            <pre class="bg-muted p-4 rounded-lg text-sm overflow-auto max-h-64 text-foreground">{{ JSON.stringify(result, null, 2) }}</pre>
          </div>
        </div>
      </DialogContent>
    </Dialog>

    <!-- Visualization Modal -->
    <Dialog v-model:open="showVisualization">
      <DialogContent class="max-w-[95vw] max-h-[95vh] w-full h-full">
        <DialogHeader>
          <DialogTitle>Text Detection Visualization</DialogTitle>
        </DialogHeader>
        <div v-if="result && result.visualization_path" class="flex-1 flex items-center justify-center overflow-hidden">
          <img
            :src="getVisualizationUrl(result.visualization_path)"
            alt="Text Detection Visualization"
            class="max-w-full max-h-full object-contain rounded-lg"
          />
        </div>
        <div class="mt-4 text-center">
          <p class="text-sm text-muted-foreground">
            Blue boxes show detected text regions with confidence scores
          </p>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { useNvidiaApiToggle } from '@/composables/useNvidiaApiToggle'

// Props
interface Props {
  nimId?: string
}

const props = withDefaults(defineProps<Props>(), {
  nimId: ''
})

// Reactive state
const uploadedFile = ref<File | null>(null)
const imagePreview = ref<string | null>(null)
const selectedNimId = ref<string>('')
const isGenerating = ref(false)
const result = ref<any>(null)
const error = ref<string | null>(null)
const showJsonModal = ref(false)
const showVisualization = ref(false)

// Use the NVIDIA API toggle composable
const { useNvidiaApi } = useNvidiaApiToggle()

// Runtime config
const config = useRuntimeConfig()

// Available PaddleOCR NIMs
const paddleocrNims = ref<any[]>([])

// Computed properties
const canGenerate = computed(() => {
  return uploadedFile.value && selectedNimId.value && !isGenerating.value
})

const requestData = computed(() => {
  if (!imagePreview.value) return {}

  return {
    image_data_url: imagePreview.value
  }
})

// Methods
const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (file) {
    uploadedFile.value = file

    // Create preview
    const reader = new FileReader()
    reader.onload = (e) => {
      imagePreview.value = e.target?.result as string
    }
    reader.readAsDataURL(file)

    // Clear previous results
    result.value = null
    error.value = null
  }
}

const clearUploadedFile = () => {
  uploadedFile.value = null
  imagePreview.value = null
  result.value = null
  error.value = null
}

const previewImage = () => {
  if (imagePreview.value) {
    // Open image in new tab
    window.open(imagePreview.value, '_blank')
  }
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getVisualizationUrl = (path: string): string => {
  // Convert backend path to frontend URL
  const relativePath = path.replace(/^.*\/media\//, '/media/')
  return `${config.public.apiBase}${relativePath}`
}

const copyResults = async () => {
  if (result.value) {
    try {
      await navigator.clipboard.writeText(JSON.stringify(result.value, null, 2))
      // You could add a toast notification here
    } catch (err) {
      console.error('Failed to copy results:', err)
    }
  }
}

const generateText = async () => {
  if (!canGenerate.value) return

  isGenerating.value = true
  error.value = null
  result.value = null

  try {
    const [publisher, modelName] = selectedNimId.value.split('/')

    const response = await fetch(`${config.public.apiBase}/v0/nims/${publisher}/${modelName}?use_nvidia_api=${useNvidiaApi.value}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestData.value),
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Failed to generate text detection')
    }

    const data = await response.json()
    result.value = data.output

  } catch (err) {
    error.value = err instanceof Error ? err.message : 'An error occurred'
    console.error('PaddleOCR generation error:', err)
  } finally {
    isGenerating.value = false
  }
}

const loadPaddleocrNims = async () => {
  try {
    // If nimId prop is provided, use it directly
    if (props.nimId) {
      selectedNimId.value = props.nimId
      paddleocrNims.value = [{ nim_id: props.nimId }]
      return
    }

    // Otherwise, load all PaddleOCR NIMs
    const response = await fetch(`${config.public.apiBase}/api/nims/`)
    const data = await response.json()

    // Filter for PaddleOCR NIMs
    paddleocrNims.value = data.nim_ids
      .filter((nimId: string) => nimId.includes('paddleocr') || nimId.includes('baidu'))
      .map((nimId: string) => ({ nim_id: nimId }))

    // Auto-select first PaddleOCR NIM if available
    if (paddleocrNims.value.length > 0) {
      selectedNimId.value = paddleocrNims.value[0].nim_id
    }
  } catch (err) {
    console.error('Failed to load PaddleOCR NIMs:', err)
  }
}

// Lifecycle
onMounted(() => {
  loadPaddleocrNims()
})
</script>
