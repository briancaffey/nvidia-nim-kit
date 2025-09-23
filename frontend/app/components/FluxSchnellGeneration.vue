<template>
  <div>
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold mb-2">
        {{ nimId === 'black-forest-labs/flux_1-schnell' ? 'Flux Schnell Image Generation' : 'Flux Dev Image Generation' }}
      </h1>
      <p class="text-muted-foreground">
        {{ nimId === 'black-forest-labs/flux_1-schnell'
           ? 'Generate high-quality images using FLUX.1-schnell model'
           : 'Generate high-quality images using FLUX.1-dev model with advanced features' }}
      </p>
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
                  Configure your image generation settings
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
              <div class="flex justify-between items-center">
                <Label for="steps">Steps</Label>
                <span class="text-sm font-medium text-muted-foreground">{{ formData.steps }}</span>
              </div>
              <Slider
                v-model="stepsValue"
                :min="isFluxSchnell ? 1 : 5"
                :max="isFluxSchnell ? 4 : 50"
                :step="1"
                class="w-full"
              />
              <p class="text-sm text-muted-foreground">
                Number of denoising steps ({{ isFluxSchnell ? '1-4' : '5-50' }})
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

            <!-- Mode Selection -->
            <div class="space-y-2">
              <Label for="mode">Mode</Label>
              <Select v-model="formData.mode">
                <SelectTrigger>
                  <SelectValue placeholder="Select mode" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="base">Base</SelectItem>
                  <SelectItem value="canny">Canny</SelectItem>
                  <SelectItem value="depth">Depth</SelectItem>
                </SelectContent>
              </Select>
              <p class="text-sm text-muted-foreground">
                Generation mode: base (text-to-image), canny (edge-guided), depth (depth-guided)
              </p>
            </div>

            <!-- Image Upload for Canny/Depth modes -->
            <div v-if="formData.mode === 'canny' || formData.mode === 'depth'" class="space-y-2">
              <Label for="image">Reference Image</Label>
              <div class="space-y-2">
                <Input
                  id="image"
                  type="file"
                  accept="image/*"
                  @change="handleImageUpload"
                  class="cursor-pointer"
                />
                <p class="text-sm text-muted-foreground">
                  Upload an image for {{ formData.mode }} mode. Image will be automatically resized to supported dimensions.
                </p>

                <!-- Image Preview and Conversion Controls -->
                <div v-if="uploadedImagePreview" class="mt-4 space-y-4">
                  <!-- Original Image Preview -->
                  <div class="space-y-2">
                    <h4 class="text-sm font-medium">Original Image</h4>
                    <img
                      :src="uploadedImagePreview"
                      alt="Uploaded image preview"
                      class="w-full max-w-xs rounded-lg border"
                    />
                    <p class="text-xs text-muted-foreground">
                      Dimensions: {{ uploadedImageDimensions?.width }}×{{ uploadedImageDimensions?.height }}
                    </p>
                  </div>

                  <!-- Canny Edge Parameters -->
                  <div v-if="formData.mode === 'canny'" class="space-y-4">
                    <h4 class="text-sm font-medium">Canny Edge Detection Parameters</h4>

                    <!-- Lower Threshold -->
                    <div class="space-y-2">
                      <Label for="canny-lower">Lower Threshold Multiplier</Label>
                      <div class="flex items-center space-x-2">
                        <Input
                          id="canny-lower"
                          v-model.number="cannyParams.canny_lower_threshold"
                          type="number"
                          step="0.1"
                          min="0.1"
                          max="1.0"
                          class="w-20"
                        />
                        <span class="text-sm text-muted-foreground">{{ cannyParams.canny_lower_threshold }}</span>
                      </div>
                      <p class="text-xs text-muted-foreground">
                        Lower threshold multiplier (0.1-1.0). Lower values detect more edges.
                      </p>
                    </div>

                    <!-- Upper Threshold -->
                    <div class="space-y-2">
                      <Label for="canny-upper">Upper Threshold Multiplier</Label>
                      <div class="flex items-center space-x-2">
                        <Input
                          id="canny-upper"
                          v-model.number="cannyParams.canny_upper_threshold"
                          type="number"
                          step="0.1"
                          min="1.0"
                          max="3.0"
                          class="w-20"
                        />
                        <span class="text-sm text-muted-foreground">{{ cannyParams.canny_upper_threshold }}</span>
                      </div>
                      <p class="text-xs text-muted-foreground">
                        Upper threshold multiplier (1.0-3.0). Higher values detect fewer, stronger edges.
                      </p>
                    </div>

                    <!-- Blur Kernel Size -->
                    <div class="space-y-2">
                      <Label for="canny-blur-kernel">Blur Kernel Size</Label>
                      <div class="flex items-center space-x-2">
                        <Input
                          id="canny-blur-kernel"
                          v-model.number="cannyParams.canny_blur_kernel_size"
                          type="number"
                          step="2"
                          min="3"
                          max="15"
                          class="w-20"
                        />
                        <span class="text-sm text-muted-foreground">{{ cannyParams.canny_blur_kernel_size }}</span>
                      </div>
                      <p class="text-xs text-muted-foreground">
                        Gaussian blur kernel size (3-15, odd numbers only). Larger values reduce noise but blur edges.
                      </p>
                    </div>

                    <!-- Blur Sigma -->
                    <div class="space-y-2">
                      <Label for="canny-blur-sigma">Blur Sigma</Label>
                      <div class="flex items-center space-x-2">
                        <Input
                          id="canny-blur-sigma"
                          v-model.number="cannyParams.canny_blur_sigma"
                          type="number"
                          step="0.1"
                          min="0.0"
                          max="5.0"
                          class="w-20"
                        />
                        <span class="text-sm text-muted-foreground">{{ cannyParams.canny_blur_sigma }}</span>
                      </div>
                      <p class="text-xs text-muted-foreground">
                        Gaussian blur sigma (0.0-5.0). 0 = auto-calculate. Higher values create more blur.
                      </p>
                    </div>
                  </div>

                  <!-- Conversion Controls -->
                  <div class="space-y-2">
                    <h4 class="text-sm font-medium">Convert Image</h4>
                    <div class="flex gap-2">
                      <Button
                        v-if="formData.mode === 'canny'"
                        @click="convertImage('canny')"
                        :disabled="convertingImage"
                        variant="outline"
                        size="sm"
                      >
                        <Icon v-if="convertingImage" name="lucide:loader-2" class="h-4 w-4 mr-2 animate-spin" />
                        <Icon v-else name="lucide:zap" class="h-4 w-4 mr-2" />
                        {{ convertingImage ? 'Converting...' : 'Convert to Canny Edges' }}
                      </Button>

                      <Button
                        v-if="formData.mode === 'depth'"
                        @click="convertImage('depth')"
                        :disabled="convertingImage"
                        variant="outline"
                        size="sm"
                      >
                        <Icon v-if="convertingImage" name="lucide:loader-2" class="h-4 w-4 mr-2 animate-spin" />
                        <Icon v-else name="lucide:layers" class="h-4 w-4 mr-2" />
                        {{ convertingImage ? 'Converting...' : 'Convert to Depth Map' }}
                      </Button>
                    </div>
                    <p class="text-xs text-muted-foreground">
                      {{ formData.mode === 'canny'
                         ? 'Extract edge features from your image for better control over the generated image structure.'
                         : 'Generate a depth map to guide the 3D structure and spatial relationships in your generated image.' }}
                    </p>
                  </div>

                  <!-- Converted Image Preview -->
                  <div v-if="convertedImagePreview" class="space-y-2">
                    <h4 class="text-sm font-medium">Converted Image</h4>
                    <img
                      :src="convertedImagePreview"
                      alt="Converted image preview"
                      class="w-full max-w-xs rounded-lg border"
                    />
                    <p class="text-xs text-muted-foreground">
                      {{ formData.mode === 'canny' ? 'Edge-detected image' : 'Depth map visualization' }}
                    </p>
                    <div class="flex gap-2">
                      <Button
                        @click="useConvertedImage"
                        variant="default"
                        size="sm"
                      >
                        <Icon name="lucide:check" class="h-4 w-4 mr-2" />
                        Use This Image
                      </Button>
                      <Button
                        @click="resetConvertedImage"
                        variant="outline"
                        size="sm"
                      >
                        <Icon name="lucide:x" class="h-4 w-4 mr-2" />
                        Reset
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
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
                    <SelectItem :value="672">672px</SelectItem>
                    <SelectItem :value="688">688px</SelectItem>
                    <SelectItem :value="720">720px</SelectItem>
                    <SelectItem :value="752">752px</SelectItem>
                    <SelectItem :value="800">800px</SelectItem>
                    <SelectItem :value="832">832px</SelectItem>
                    <SelectItem :value="880">880px</SelectItem>
                    <SelectItem :value="944">944px</SelectItem>
                    <SelectItem :value="1024">1024px</SelectItem>
                    <SelectItem :value="1104">1104px</SelectItem>
                    <SelectItem :value="1184">1184px</SelectItem>
                    <SelectItem :value="1248">1248px</SelectItem>
                    <SelectItem :value="1328">1328px</SelectItem>
                    <SelectItem :value="1392">1392px</SelectItem>
                    <SelectItem :value="1456">1456px</SelectItem>
                    <SelectItem :value="1504">1504px</SelectItem>
                    <SelectItem :value="1568">1568px</SelectItem>
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
                    <SelectItem :value="672">672px</SelectItem>
                    <SelectItem :value="688">688px</SelectItem>
                    <SelectItem :value="720">720px</SelectItem>
                    <SelectItem :value="752">752px</SelectItem>
                    <SelectItem :value="800">800px</SelectItem>
                    <SelectItem :value="832">832px</SelectItem>
                    <SelectItem :value="880">880px</SelectItem>
                    <SelectItem :value="944">944px</SelectItem>
                    <SelectItem :value="1024">1024px</SelectItem>
                    <SelectItem :value="1104">1104px</SelectItem>
                    <SelectItem :value="1184">1184px</SelectItem>
                    <SelectItem :value="1248">1248px</SelectItem>
                    <SelectItem :value="1328">1328px</SelectItem>
                    <SelectItem :value="1392">1392px</SelectItem>
                    <SelectItem :value="1456">1456px</SelectItem>
                    <SelectItem :value="1504">1504px</SelectItem>
                    <SelectItem :value="1568">1568px</SelectItem>
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
import { Slider } from '~/components/ui/slider'

interface Props {
  nimId: string
}

const props = defineProps<Props>()

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

// Separate interface for canny parameters (not sent to NIM)
interface CannyParams {
  canny_lower_threshold: number
  canny_upper_threshold: number
  canny_blur_kernel_size: number
  canny_blur_sigma: number
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

// Form data (sent to NIM)
const formData = ref<FormData>({
  prompt: '',
  steps: 4, // Default for Flux Schnell, will be adjusted based on model
  cfg_scale: 0,
  height: 1024,
  width: 1024,
  mode: 'base',
  image: null,
  samples: 1,
  seed: 0
})

// Canny edge detection parameters (only used for image conversion)
const cannyParams = ref<CannyParams>({
  canny_lower_threshold: 0.7,
  canny_upper_threshold: 1.3,
  canny_blur_kernel_size: 5,
  canny_blur_sigma: 0.0
})

// State
const loading = ref(false)
const error = ref<string | null>(null)
const generatedImage = ref<string | null>(null)
const inferenceResult = ref<InferenceResult | null>(null)
const showJsonModal = ref(false)
const contentFiltered = ref(false)
const uploadedImagePreview = ref<string | null>(null)
const uploadedImageDimensions = ref<{width: number, height: number} | null>(null)
const convertedImagePreview = ref<string | null>(null)
const convertingImage = ref(false)

// Use NIM ID from props
const nimId = computed(() => props.nimId)

// Check if this is Flux Schnell model
const isFluxSchnell = computed(() => nimId.value === 'black-forest-labs/flux_1-schnell')

// Computed property to handle slider array format
const stepsValue = computed({
  get: () => [formData.value.steps],
  set: (value: number[]) => {
    formData.value.steps = value[0]
  }
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

    const toggleResponse = await fetch(`${config.public.apiBase}/api/nvidia/toggle`)
    const toggleData = await toggleResponse.json()
    const useNvidiaApi = toggleData.enabled

    const response = await $fetch<InferenceResult>(`${config.public.apiBase}/v0/nims/${nimId.value}?use_nvidia_api=${useNvidiaApi}`, {
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

// Supported dimensions for Flux models
const supportedDimensions = [672, 688, 720, 752, 800, 832, 880, 944, 1024, 1104, 1184, 1248, 1328, 1392, 1456, 1504, 1568]

// Find the closest supported dimension
const findClosestDimension = (value: number): number => {
  return supportedDimensions.reduce((prev, curr) =>
    Math.abs(curr - value) < Math.abs(prev - value) ? curr : prev
  )
}

// Resize and crop image to supported dimensions
const resizeImageToSupportedDimensions = (file: File): Promise<{dataUrl: string, width: number, height: number}> => {
  return new Promise((resolve, reject) => {
    const img = new Image()
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')

    if (!ctx) {
      reject(new Error('Could not get canvas context'))
      return
    }

    img.onload = () => {
      // Find closest supported dimensions
      const targetWidth = findClosestDimension(img.width)
      const targetHeight = findClosestDimension(img.height)

      // Set canvas size
      canvas.width = targetWidth
      canvas.height = targetHeight

      // Calculate scaling to maintain aspect ratio while fitting in target dimensions
      const scaleX = targetWidth / img.width
      const scaleY = targetHeight / img.height
      const scale = Math.min(scaleX, scaleY)

      // Calculate centered position
      const scaledWidth = img.width * scale
      const scaledHeight = img.height * scale
      const x = (targetWidth - scaledWidth) / 2
      const y = (targetHeight - scaledHeight) / 2

      // Draw image centered and scaled
      ctx.drawImage(img, x, y, scaledWidth, scaledHeight)

      // Convert to data URL
      const dataUrl = canvas.toDataURL('image/jpeg', 0.9)

      resolve({
        dataUrl,
        width: targetWidth,
        height: targetHeight
      })
    }

    img.onerror = () => reject(new Error('Failed to load image'))
    img.src = URL.createObjectURL(file)
  })
}

// Handle image upload
const handleImageUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (!file) {
    formData.value.image = null
    uploadedImagePreview.value = null
    uploadedImageDimensions.value = null
    convertedImagePreview.value = null
    return
  }

  try {
    const { dataUrl, width, height } = await resizeImageToSupportedDimensions(file)

    // Send the full data URL (including the data:image/... prefix)
    // This is what the Flux Dev model expects
    formData.value.image = dataUrl
    formData.value.width = width
    formData.value.height = height

    // Update preview
    uploadedImagePreview.value = dataUrl
    uploadedImageDimensions.value = { width, height }

    // Reset converted image when new image is uploaded
    convertedImagePreview.value = null

  } catch (error) {
    console.error('Failed to process image:', error)
    // Reset form data
    formData.value.image = null
    uploadedImagePreview.value = null
    uploadedImageDimensions.value = null
    convertedImagePreview.value = null
  }
}

// Convert image to canny edges or depth map
const convertImage = async (conversionType: 'canny' | 'depth') => {
  if (!uploadedImagePreview.value) {
    console.error('No image to convert')
    return
  }

  try {
    convertingImage.value = true
    console.log(`🎨 Starting ${conversionType} conversion`)

    const requestBody: any = {
      image_data: uploadedImagePreview.value,
      conversion_type: conversionType
    }

    // Add canny parameters if converting to canny
    if (conversionType === 'canny') {
      requestBody.canny_lower_threshold = cannyParams.value.canny_lower_threshold
      requestBody.canny_upper_threshold = cannyParams.value.canny_upper_threshold
      requestBody.canny_blur_kernel_size = cannyParams.value.canny_blur_kernel_size
      requestBody.canny_blur_sigma = cannyParams.value.canny_blur_sigma
    }

    const response = await $fetch<{
      converted_image_data: string
      original_dimensions: {width: number, height: number}
      converted_dimensions: {width: number, height: number}
    }>(`${config.public.apiBase}/v0/image-conversion/convert`, {
      method: 'POST',
      body: requestBody
    })

    console.log(`✅ ${conversionType} conversion completed:`, response)

    // Update converted image preview
    convertedImagePreview.value = response.converted_image_data

  } catch (err: any) {
    console.error(`❌ ${conversionType} conversion failed:`, err)
    error.value = `Image conversion failed: ${err.data?.detail || err.message || 'Unknown error'}`
  } finally {
    convertingImage.value = false
  }
}

// Use the converted image for generation
const useConvertedImage = () => {
  if (!convertedImagePreview.value) return

  // Update form data with converted image
  formData.value.image = convertedImagePreview.value

  console.log('✅ Using converted image for generation')
}

// Reset converted image
const resetConvertedImage = () => {
  convertedImagePreview.value = null
  console.log('🔄 Reset converted image')
}

// Watch for canny parameter changes and auto-convert if we have a converted image
watch([
  () => cannyParams.value.canny_lower_threshold,
  () => cannyParams.value.canny_upper_threshold,
  () => cannyParams.value.canny_blur_kernel_size,
  () => cannyParams.value.canny_blur_sigma
], async () => {
  // Only auto-convert if we're in canny mode, have an uploaded image, and already have a converted image
  if (formData.value.mode === 'canny' &&
      uploadedImagePreview.value &&
      convertedImagePreview.value &&
      !convertingImage.value) {
    console.log('🔄 Canny parameters changed, re-converting image...')
    await convertImage('canny')
  }
}, { deep: true })

// Watch for model changes and adjust steps accordingly
watch(isFluxSchnell, (isSchnell) => {
  if (isSchnell) {
    // Flux Schnell: 1-4, default 4
    if (formData.value.steps > 4) {
      formData.value.steps = 4
    }
  } else {
    // Flux Dev: 5-50, default 20
    if (formData.value.steps < 5) {
      formData.value.steps = 20
    }
  }
}, { immediate: true })

// Set page metadata
useHead({
  title: computed(() => nimId.value === 'black-forest-labs/flux_1-schnell'
    ? 'Flux Schnell Generation - NIM Kit'
    : 'Flux Dev Generation - NIM Kit'),
  meta: [
    {
      name: 'description',
      content: computed(() => nimId.value === 'black-forest-labs/flux_1-schnell'
        ? 'Generate high-quality images using FLUX.1-schnell model'
        : 'Generate high-quality images using FLUX.1-dev model with advanced features')
    }
  ]
})
</script>
