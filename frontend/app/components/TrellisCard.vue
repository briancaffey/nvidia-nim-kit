<template>
  <div class="space-y-3">
    <!-- Prompt Display (if available) -->
    <div v-if="inputData.prompt" class="text-sm">
      <h4 class="font-medium text-gray-900 dark:text-white mb-2">Prompt</h4>
      <div class="bg-gray-50 dark:bg-gray-800 rounded p-3">
        <p class="text-gray-900 dark:text-white">{{ inputData.prompt }}</p>
      </div>
    </div>

    <!-- 3D Model Display -->
    <div v-if="request.status === 'completed' && modelUrl" class="text-sm">
      <h4 class="font-medium text-gray-900 dark:text-white mb-2">Generated 3D Model</h4>
      <div class="w-full h-64 bg-muted rounded-lg overflow-hidden">
        <ClientOnly>
          <TresCanvas :clear-color="sceneBackgroundColor">
            <TresPerspectiveCamera :position="[2, 2, 2]" />
            <OrbitControls />

            <!-- 3D Model -->
            <TresGroup ref="modelGroup">
              <!-- Model will be added programmatically -->
            </TresGroup>

            <!-- Lighting -->
            <TresAmbientLight :intensity="5.0" />
            <TresHemisphereLight
              :sky-color="0xffffff"
              :ground-color="0x444444"
              :intensity="1.5"
            />
            <TresDirectionalLight :position="[5, 5, 5]" :intensity="3.0" />
            <TresDirectionalLight :position="[-5, -5, -5]" :intensity="2.5" />
            <TresDirectionalLight :position="[0, 10, 0]" :intensity="2.8" />
            <TresDirectionalLight :position="[0, -10, 0]" :intensity="2.5" />
            <TresDirectionalLight :position="[10, 0, 0]" :intensity="2.5" />
            <TresDirectionalLight :position="[-10, 0, 0]" :intensity="2.5" />
            <TresDirectionalLight :position="[0, 0, 10]" :intensity="2.5" />
            <TresDirectionalLight :position="[0, 0, -10]" :intensity="2.5" />
          </TresCanvas>
          <template #fallback>
            <div class="w-full h-full flex items-center justify-center text-muted-foreground">
              Loading 3D model...
            </div>
          </template>
        </ClientOnly>
      </div>

      <!-- Download Button -->
      <Button
        @click="downloadModel"
        variant="outline"
        size="sm"
        class="w-full mt-2"
      >
        <Icon name="lucide:download" class="h-4 w-4 mr-2" />
        Download GLB Model
      </Button>
    </div>

    <!-- Error Display -->
    <div v-if="request.error_data && Object.keys(request.error_data).length > 0" class="text-sm">
      <h4 class="font-medium text-red-600 dark:text-red-400 mb-2">Error Data</h4>
      <div class="bg-red-50 dark:bg-red-900/20 rounded p-3 max-h-32 overflow-y-auto">
        <pre class="text-xs text-red-700 dark:text-red-300 whitespace-pre-wrap">{{ formatJson(request.error_data) }}</pre>
      </div>
    </div>

    <!-- Generation Parameters as Badges -->
    <div class="text-sm">
      <h4 class="font-medium text-gray-900 dark:text-white mb-2">Parameters</h4>
      <div class="flex flex-wrap gap-2">
        <Badge variant="secondary" class="text-xs">
          Mode: {{ inputData.mode }}
        </Badge>
        <Badge variant="secondary" class="text-xs">
          CFG: {{ inputData.slat_cfg_scale }}
        </Badge>
        <Badge variant="secondary" class="text-xs">
          SS CFG: {{ inputData.ss_cfg_scale }}
        </Badge>
        <Badge variant="secondary" class="text-xs">
          Seed: {{ inputData.seed }}
        </Badge>
        <Badge variant="secondary" class="text-xs">
          Format: {{ inputData.output_format }}
        </Badge>
        <Badge variant="secondary" class="text-xs">
          Texture: {{ inputData.no_texture ? 'Off' : 'On' }}
        </Badge>
        <Badge v-if="inputData.ss_sampling_steps" variant="secondary" class="text-xs">
          SS Steps: {{ inputData.ss_sampling_steps }}
        </Badge>
        <Badge v-if="inputData.slat_sampling_steps" variant="secondary" class="text-xs">
          Latent Steps: {{ inputData.slat_sampling_steps }}
        </Badge>
        <Badge v-if="inputData.samples" variant="secondary" class="text-xs">
          Samples: {{ inputData.samples }}
        </Badge>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { OrbitControls } from '@tresjs/cientos'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import * as THREE from 'three'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Icon } from '#components'

// Disable SSR for this component since TresJS is client-side only
definePageMeta({
  ssr: false
})

// Props
interface Props {
  request: {
    request_id: string
    type: string
    request_type: string
    nim_id: string
    model: string
    stream: boolean
    status: string
    date_created: string
    date_updated: string
    input_data: any
    output_data: any
    error_data: any
  }
}

const props = defineProps<Props>()

// Composables
const config = useRuntimeConfig()
const colorMode = useColorMode()

// Computed properties
const inputData = computed(() => props.request.input_data || {})
const modelUrl = computed(() => {
  if (props.request.status === 'completed') {
    return `${config.public.apiBase}/media/models/${props.request.request_id}.glb`
  }
  return null
})

const sceneBackgroundColor = computed(() => {
  return colorMode.value === 'dark' ? '#1a1a1a' : '#f8f9fa'
})

// 3D Model loading
const modelScene = shallowRef<any>(null)
const modelGroup = ref<any>(null)

// Methods
const formatJson = (data: any) => {
  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return String(data)
  }
}

const load3DModel = async (url: string) => {
  try {
    console.log('Loading 3D model from:', url)
    const loader = new GLTFLoader()
    const gltf = await loader.loadAsync(url)

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

    // Add the model to the TresGroup
    if (modelGroup.value) {
      modelGroup.value.clear()
      modelGroup.value.add(scene)
    } else {
      setTimeout(() => {
        if (modelGroup.value) {
          modelGroup.value.clear()
          modelGroup.value.add(scene)
        }
      }, 100)
    }

    modelScene.value = scene
    console.log('3D model loaded and centered successfully')
  } catch (error) {
    console.error('Failed to load 3D model:', error)
  }
}

const downloadModel = () => {
  if (!modelUrl.value) return

  const link = document.createElement('a')
  link.href = modelUrl.value
  link.download = `trellis-model-${props.request.request_id}.glb`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// Dispose of previous model
const disposeModel = () => {
  if (modelGroup.value) {
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

// Load 3D model when component mounts and modelUrl is available
watch(modelUrl, (newUrl) => {
  if (newUrl) {
    load3DModel(newUrl)
  }
}, { immediate: true })

// Cleanup on component unmount
onUnmounted(() => {
  disposeModel()
})
</script>
