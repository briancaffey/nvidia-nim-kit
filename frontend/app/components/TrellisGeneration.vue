<template>
  <div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Left Side - Form -->
      <div class="space-y-6">
        <Card>
          <CardHeader>
            <div class="flex justify-between items-start">
              <div>
                <CardTitle>Generation Parameters</CardTitle>
                <CardDescription>
                  Configure your 3D model generation settings
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

            <!-- Mode Selection -->
            <div class="space-y-2">
              <Label for="mode">Mode</Label>
              <Select v-model="formData.mode">
                <SelectTrigger>
                  <SelectValue placeholder="Select mode" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="text">Text</SelectItem>
                  <SelectItem value="image">Image</SelectItem>
                </SelectContent>
              </Select>
              <p class="text-sm text-muted-foreground">
                Choose between text-to-3D or image-to-3D generation
              </p>
            </div>

            <!-- Prompt Input (only for text mode) -->
            <div v-if="formData.mode === 'text'" class="space-y-2">
              <Label for="prompt">Prompt</Label>
              <Textarea
                id="prompt"
                v-model="formData.prompt"
                placeholder="Enter your 3D model generation prompt..."
                class="min-h-[60px]"
                rows="2"
              />
            </div>

            <!-- Image Upload (only for image mode) -->
            <div v-if="formData.mode === 'image'" class="space-y-2">
              <Label for="image">Input Image</Label>
              <div class="space-y-4">
                <Input
                  id="image"
                  type="file"
                  accept="image/*"
                  @change="handleImageUpload"
                  class="cursor-pointer"
                />

                <!-- Image Preview -->
                <div v-if="uploadedImagePreview" class="space-y-2">
                  <Label>Image Preview</Label>
                  <div class="relative w-full h-48 bg-muted rounded-lg overflow-hidden">
                    <img
                      :src="uploadedImagePreview"
                      alt="Uploaded image preview"
                      class="w-full h-full object-contain"
                    />
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    @click="clearImage"
                    class="w-full"
                  >
                    <Icon name="lucide:x" class="h-4 w-4 mr-2" />
                    Clear Image
                  </Button>
                </div>
              </div>
            </div>

            <!-- CFG Scale Input -->
            <div class="space-y-2">
              <div class="flex justify-between items-center">
                <Label for="slat_cfg_scale">CFG Scale</Label>
                <span class="text-sm font-medium text-muted-foreground">{{ formData.slat_cfg_scale }}</span>
              </div>
              <Slider
                v-model="slatCfgScaleValue"
                :min="2"
                :max="10"
                :step="0.1"
                class="w-full"
              />
              <p class="text-sm text-muted-foreground">
                Classifier-free guidance scale (2.0 - 10.0)
              </p>
            </div>

            <!-- Sparse Structure CFG Scale Input -->
            <div class="space-y-2">
              <div class="flex justify-between items-center">
                <Label for="ss_cfg_scale">Sparse Structure CFG Scale</Label>
                <span class="text-sm font-medium text-muted-foreground">{{ formData.ss_cfg_scale }}</span>
              </div>
              <Slider
                v-model="ssCfgScaleValue"
                :min="2"
                :max="10"
                :step="0.1"
                class="w-full"
              />
              <p class="text-sm text-muted-foreground">
                Sparse structure classifier-free guidance scale (2.0 - 10.0)
              </p>
            </div>

            <!-- Latent Sampling Steps -->
            <div class="space-y-2">
              <div class="flex justify-between items-center">
                <Label for="slat_sampling_steps">Latent Sampling Steps</Label>
                <span class="text-sm font-medium text-muted-foreground">{{ formData.slat_sampling_steps }}</span>
              </div>
              <Slider
                v-model="slatSamplingStepsValue"
                :min="10"
                :max="50"
                :step="1"
                class="w-full"
              />
              <p class="text-sm text-muted-foreground">
                Number of latent sampling steps (10 - 50)
              </p>
            </div>

            <!-- Sparse Structure Sampling Steps -->
            <div class="space-y-2">
              <div class="flex justify-between items-center">
                <Label for="ss_sampling_steps">Sparse Structure Sampling Steps</Label>
                <span class="text-sm font-medium text-muted-foreground">{{ formData.ss_sampling_steps }}</span>
              </div>
              <Slider
                v-model="ssSamplingStepsValue"
                :min="10"
                :max="50"
                :step="1"
                class="w-full"
              />
              <p class="text-sm text-muted-foreground">
                Number of sparse structure sampling steps (10 - 50)
              </p>
            </div>

            <!-- Seed Input -->
            <div class="space-y-2">
              <Label for="seed">Seed</Label>
              <Input
                id="seed"
                v-model.number="formData.seed"
                type="number"
                min="0"
                step="1"
                placeholder="0"
              />
              <p class="text-sm text-muted-foreground">
                Random seed for reproducible results (non-negative integer)
              </p>
            </div>

            <!-- Output Format -->
            <div class="space-y-2">
              <Label for="output_format">Output Format</Label>
              <Select v-model="formData.output_format">
                <SelectTrigger>
                  <SelectValue placeholder="Select output format" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="glb">GLB</SelectItem>
                </SelectContent>
              </Select>
              <p class="text-sm text-muted-foreground">
                Output format for the 3D model
              </p>
            </div>

            <!-- No Texture Option -->
            <div class="space-y-2">
              <div class="flex items-center space-x-2">
                <Switch
                  id="no_texture"
                  v-model="formData.no_texture"
                />
                <Label for="no_texture">No Texture</Label>
              </div>
              <p class="text-sm text-muted-foreground">
                Generate model without textures (default: false)
              </p>
            </div>

            <!-- Generate Button -->
            <Button
              @click="generateModel"
              :disabled="loading || !canGenerate"
              class="w-full"
              size="lg"
            >
              <Icon v-if="loading" name="lucide:loader-2" class="h-4 w-4 mr-2 animate-spin" />
              <Icon v-else name="lucide:box" class="h-4 w-4 mr-2" />
              {{ loading ? 'Generating 3D Model...' : 'Generate 3D Model' }}
            </Button>

            <!-- Error Display -->
            <div v-if="error" class="p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
              <div class="flex items-center gap-2 text-destructive">
                <Icon name="lucide:alert-circle" class="h-4 w-4" />
                <span class="font-medium">Generation Failed</span>
              </div>
              <p class="text-sm text-destructive mt-1">{{ error }}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- Right Side - Results -->
      <div class="space-y-6">
        <!-- Generated 3D Model -->
        <Card v-if="generatedModelUrl || loading">
          <CardHeader>
            <CardTitle>Generated 3D Model</CardTitle>
            <CardDescription>
              {{ loading ? 'Generating your 3D model...' : 'Your generated 3D model' }}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div v-if="loading" class="w-full h-96 bg-muted rounded-lg flex items-center justify-center">
              <div class="text-center">
                <Icon name="lucide:loader-2" class="h-8 w-8 animate-spin mx-auto mb-4" />
                <p class="text-muted-foreground">Generating 3D model...</p>
                <p class="text-sm text-muted-foreground mt-2">This may take several minutes</p>
              </div>
            </div>

            <div v-else-if="generatedModelUrl" class="w-full h-96 bg-muted rounded-lg overflow-hidden">
              <ClientOnly>
                <TresCanvas :clear-color="sceneBackgroundColor">
                  <TresPerspectiveCamera :position="[2, 2, 2]" />
                  <OrbitControls />

                  <!-- 3D Model with proper scaling and positioning -->
                  <TresGroup ref="modelGroup">
                    <!-- Model will be added programmatically -->
                  </TresGroup>

                  <!-- Comprehensive Multi-Directional Lighting -->
                  <TresAmbientLight :intensity="5.0" />
                  <TresHemisphereLight
                    :sky-color="0xffffff"
                    :ground-color="0x444444"
                    :intensity="1.5"
                  />

                  <!-- Directional Lights from All Sides -->
                  <TresDirectionalLight :position="[5, 5, 5]" :intensity="3.0" />
                  <TresDirectionalLight :position="[-5, -5, -5]" :intensity="2.5" />
                  <TresDirectionalLight :position="[0, 10, 0]" :intensity="2.8" />
                  <TresDirectionalLight :position="[0, -10, 0]" :intensity="2.5" />
                  <TresDirectionalLight :position="[10, 0, 0]" :intensity="2.5" />
                  <TresDirectionalLight :position="[-10, 0, 0]" :intensity="2.5" />
                  <TresDirectionalLight :position="[0, 0, 10]" :intensity="2.5" />
                  <TresDirectionalLight :position="[0, 0, -10]" :intensity="2.5" />

                  <!-- Point Lights Around the Model -->
                  <TresPointLight :position="[3, 3, 3]" :intensity="2.0" />
                  <TresPointLight :position="[-3, 3, -3]" :intensity="2.0" />
                  <TresPointLight :position="[3, -3, 3]" :intensity="2.0" />
                  <TresPointLight :position="[-3, -3, -3]" :intensity="2.0" />
                  <TresPointLight :position="[0, 5, 0]" :intensity="2.5" />
                  <TresPointLight :position="[0, -5, 0]" :intensity="2.0" />
                  <TresPointLight :position="[5, 0, 0]" :intensity="2.0" />
                  <TresPointLight :position="[-5, 0, 0]" :intensity="2.0" />
                  <TresPointLight :position="[0, 0, 5]" :intensity="2.0" />
                  <TresPointLight :position="[0, 0, -5]" :intensity="2.0" />

                  <!-- Additional Corner Lights -->
                  <TresPointLight :position="[4, 4, 4]" :intensity="1.5" />
                  <TresPointLight :position="[-4, 4, 4]" :intensity="1.5" />
                  <TresPointLight :position="[4, -4, 4]" :intensity="1.5" />
                  <TresPointLight :position="[-4, -4, 4]" :intensity="1.5" />
                  <TresPointLight :position="[4, 4, -4]" :intensity="1.5" />
                  <TresPointLight :position="[-4, 4, -4]" :intensity="1.5" />
                  <TresPointLight :position="[4, -4, -4]" :intensity="1.5" />
                  <TresPointLight :position="[-4, -4, -4]" :intensity="1.5" />
                </TresCanvas>
                <template #fallback>
                  <div class="w-full h-full flex items-center justify-center text-muted-foreground">
                    Loading 3D model...
                  </div>
                </template>
              </ClientOnly>
            </div>
          </CardContent>
        </Card>

        <!-- Inference Result Details -->
        <Card v-if="inferenceResult">
          <CardHeader>
            <CardTitle>Generation Details</CardTitle>
            <CardDescription>
              Information about your 3D model generation
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span class="font-medium">Request ID:</span>
                <p class="text-muted-foreground">{{ inferenceResult.request_id }}</p>
              </div>
              <div>
                <span class="font-medium">Status:</span>
                <Badge :variant="inferenceResult.status === 'completed' ? 'default' : 'secondary'">
                  {{ inferenceResult.status }}
                </Badge>
              </div>
              <div>
                <span class="font-medium">Model:</span>
                <p class="text-muted-foreground">{{ inferenceResult.model }}</p>
              </div>
              <div>
                <span class="font-medium">Created:</span>
                <p class="text-muted-foreground">{{ formatDate(inferenceResult.date_created) }}</p>
              </div>
            </div>

            <!-- Download Button -->
            <Button
              v-if="generatedModelUrl"
              @click="downloadModel"
              variant="outline"
              class="w-full"
            >
              <Icon name="lucide:download" class="h-4 w-4 mr-2" />
              Download GLB Model
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>

    <!-- JSON Modal -->
    <Dialog v-model:open="showJsonModal">
      <DialogContent class="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Request JSON</DialogTitle>
          <DialogDescription>
            The JSON payload that will be sent to the Trellis API
          </DialogDescription>
        </DialogHeader>
        <div class="space-y-4">
          <pre class="bg-muted p-4 rounded-lg text-sm overflow-auto max-h-96">{{ JSON.stringify(getPayloadForDisplay(), null, 2) }}</pre>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { OrbitControls } from '@tresjs/cientos'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import * as THREE from 'three'

// Disable SSR for this component since TresJS is client-side only
definePageMeta({
  ssr: false
})

// Props
interface Props {
  nimId: string
}

const props = defineProps<Props>()

// Composables
const config = useRuntimeConfig()
const colorMode = useColorMode()

// Reactive data
const formData = ref({
  mode: 'text',
  prompt: '',
  image: null as string | null,
  ss_cfg_scale: 7.5,
  slat_cfg_scale: 3.0,
  samples: 1,
  no_texture: false,
  seed: 0,
  ss_sampling_steps: 25,
  slat_sampling_steps: 25,
  output_format: 'glb'
})

const loading = ref(false)
const error = ref<string | null>(null)
const generatedModelUrl = ref<string | null>(null)
const inferenceResult = ref<any>(null)
const showJsonModal = ref(false)
const uploadedImagePreview = ref<string | null>(null)

// Computed properties
const canGenerate = computed(() => {
  if (formData.value.mode === 'text') {
    return formData.value.prompt.trim().length > 0
  } else {
    return formData.value.image !== null
  }
})

const sceneBackgroundColor = computed(() => {
  return colorMode.value === 'dark' ? '#1a1a1a' : '#f8f9fa'
})

// Slider computed properties
const slatCfgScaleValue = computed({
  get: () => [formData.value.slat_cfg_scale],
  set: (value: number[]) => {
    formData.value.slat_cfg_scale = value[0] || 3.0
  }
})

const ssCfgScaleValue = computed({
  get: () => [formData.value.ss_cfg_scale],
  set: (value: number[]) => {
    formData.value.ss_cfg_scale = value[0] || 7.5
  }
})

const slatSamplingStepsValue = computed({
  get: () => [formData.value.slat_sampling_steps],
  set: (value: number[]) => {
    formData.value.slat_sampling_steps = value[0] || 25
  }
})

const ssSamplingStepsValue = computed({
  get: () => [formData.value.ss_sampling_steps],
  set: (value: number[]) => {
    formData.value.ss_sampling_steps = value[0] || 25
  }
})

// 3D Model loading
const modelScene = shallowRef<any>(null)
const modelGroup = ref<any>(null)

// Dispose of previous model
const disposeModel = () => {
  if (modelGroup.value) {
    // Clear the group
    modelGroup.value.clear()
  }

  if (modelScene.value) {
    modelScene.value.traverse((child: any) => {
      if (child.geometry) {
        child.geometry.dispose()
      }
      if (child.material) {
        if (Array.isArray(child.material)) {
          child.material.forEach((material: any) => material.dispose())
        } else {
          child.material.dispose()
        }
      }
    })
    modelScene.value = null
  }
}

// Methods
const getPayloadForDisplay = () => {
  // Prepare payload - only include relevant fields based on mode
  const payload: any = {
    mode: formData.value.mode,
    ss_cfg_scale: formData.value.ss_cfg_scale,
    slat_cfg_scale: formData.value.slat_cfg_scale,
    samples: formData.value.samples,
    no_texture: formData.value.no_texture,
    seed: formData.value.seed,
    ss_sampling_steps: formData.value.ss_sampling_steps,
    slat_sampling_steps: formData.value.slat_sampling_steps,
    output_format: formData.value.output_format
  }

  // Add mode-specific fields
  if (formData.value.mode === 'text') {
    payload.prompt = formData.value.prompt
  } else if (formData.value.mode === 'image') {
    payload.image = formData.value.image
  }

  // Don't include image in display if it's too long
  if (payload.image && payload.image.length > 100) {
    payload.image = payload.image.substring(0, 100) + '...'
  }
  return payload
}

const generateModel = async () => {
  if (!canGenerate.value) {
    error.value = 'Please provide a prompt or upload an image'
    return
  }

  try {
    loading.value = true
    error.value = null
    generatedModelUrl.value = null
    inferenceResult.value = null

    // Prepare payload - only include relevant fields based on mode
    const payload: any = {
      mode: formData.value.mode,
      ss_cfg_scale: formData.value.ss_cfg_scale,
      slat_cfg_scale: formData.value.slat_cfg_scale,
      samples: formData.value.samples,
      no_texture: formData.value.no_texture,
      seed: formData.value.seed,
      ss_sampling_steps: formData.value.ss_sampling_steps,
      slat_sampling_steps: formData.value.slat_sampling_steps,
      output_format: formData.value.output_format
    }

    // Add mode-specific fields
    if (formData.value.mode === 'text') {
      payload.prompt = formData.value.prompt
    } else if (formData.value.mode === 'image') {
      payload.image = formData.value.image
    }

    console.log('Generating 3D model with data:', payload)

    const toggleResponse = await fetch(`${config.public.apiBase}/api/nvidia/toggle`)
    const toggleData = await toggleResponse.json()
    const useNvidiaApi = toggleData.enabled

    const response = await $fetch<any>(`${config.public.apiBase}/v0/nims/${props.nimId}?use_nvidia_api=${useNvidiaApi}`, {
      method: 'POST',
      body: payload
    })

    console.log('Generation response:', response)
    inferenceResult.value = response

    // Extract GLB model URL from response
    if (response.status === 'completed') {
      // Construct the GLB file URL based on the request ID
      const glbUrl = `${config.public.apiBase}/media/models/${response.request_id}.glb`
      generatedModelUrl.value = glbUrl

      // Load the 3D model
      await load3DModel(glbUrl)
    }

  } catch (err: any) {
    console.error('3D model generation failed:', err)
    error.value = err.data?.detail || err.message || '3D model generation failed'
  } finally {
    loading.value = false
  }
}

const load3DModel = async (url: string) => {
  try {
    console.log('Loading 3D model from:', url)
    const loader = new GLTFLoader()
    const gltf = await loader.loadAsync(url)

    // Use the scene directly without cloning to avoid reactivity issues
    const scene = gltf.scene

    // Center and scale the model
    const box = new THREE.Box3().setFromObject(scene)
    const center = box.getCenter(new THREE.Vector3())
    const size = box.getSize(new THREE.Vector3())

    // Center the model
    scene.position.sub(center)

    // Scale the model to fit in a reasonable size (max dimension = 2 units)
    const maxDimension = Math.max(size.x, size.y, size.z)
    if (maxDimension > 0) {
      const scale = 2 / maxDimension
      scene.scale.setScalar(scale)
    }

    // Add the model directly to the TresGroup to avoid reactivity issues
    if (modelGroup.value) {
      // Clear any existing models
      modelGroup.value.clear()
      // Add the new model
      modelGroup.value.add(scene)
    } else {
      // If modelGroup is not ready, wait a bit and try again
      setTimeout(() => {
        if (modelGroup.value) {
          modelGroup.value.clear()
          modelGroup.value.add(scene)
        }
      }, 100)
    }

    // Also store reference for disposal
    modelScene.value = scene
    console.log('3D model loaded and centered successfully')
  } catch (error) {
    console.error('Failed to load 3D model:', error)
  }
}

const handleImageUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (!file) {
    formData.value.image = null
    uploadedImagePreview.value = null
    return
  }

  try {
    // Convert file to base64 data URL
    const dataUrl = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result as string)
      reader.onerror = reject
      reader.readAsDataURL(file)
    })

    formData.value.image = dataUrl
    uploadedImagePreview.value = dataUrl

  } catch (error) {
    console.error('Failed to process image:', error)
    formData.value.image = null
    uploadedImagePreview.value = null
  }
}

const clearImage = () => {
  formData.value.image = null
  uploadedImagePreview.value = null
}

const downloadModel = () => {
  if (!generatedModelUrl.value) return

  const link = document.createElement('a')
  link.href = generatedModelUrl.value
  link.download = `trellis-model-${inferenceResult.value?.request_id || 'generated'}.glb`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}

// Watch for mode changes to clear prompt when switching to image mode
watch(() => formData.value.mode, (newMode) => {
  if (newMode === 'image') {
    formData.value.prompt = ''
  }
})

// Cleanup on component unmount
onUnmounted(() => {
  disposeModel()
})
</script>
