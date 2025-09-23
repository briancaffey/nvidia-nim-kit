<template>
  <div class="container mx-auto px-4 py-8">
    <div class="max-w-4xl mx-auto">
      <!-- Page Header -->
      <div class="text-center mb-8">
        <h1 class="text-4xl font-bold mb-4">TresJS Testing</h1>
        <p class="text-muted-foreground text-lg">
          Interactive NVIDIA RTX 5090 3D model with orbit controls powered by TresJS
        </p>
      </div>

      <!-- 3D Scene Card -->
      <Card class="w-full">
        <CardHeader>
          <CardTitle class="text-center">NVIDIA RTX 5090 3D Model</CardTitle>
          <CardDescription class="text-center">
            Use mouse to rotate, zoom, and pan around the RTX 5090 graphics card
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div class="w-full h-96 bg-muted rounded-lg overflow-hidden">
            <ClientOnly>
              <TresCanvas :clear-color="sceneBackgroundColor">
                <TresPerspectiveCamera :position="[2, 2, 2]" />
                <OrbitControls />

                <!-- 3D Model with enhanced visibility -->
                <primitive v-if="modelScene" :object="modelScene" :scale="[0.1, 0.1, 0.1]" :position="[0, 0, 0]" />

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
                  Loading 3D scene...
                </div>
              </template>
            </ClientOnly>
          </div>
        </CardContent>
      </Card>

      <!-- Instructions -->
      <Card class="mt-6">
        <CardHeader>
          <CardTitle>Controls</CardTitle>
        </CardHeader>
        <CardContent>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 class="font-semibold mb-2">Mouse Controls</h4>
              <ul class="text-sm text-muted-foreground space-y-1">
                <li>• Left click + drag: Rotate camera</li>
                <li>• Right click + drag: Pan camera</li>
                <li>• Scroll wheel: Zoom in/out</li>
              </ul>
            </div>
            <div>
              <h4 class="font-semibold mb-2">Features</h4>
              <ul class="text-sm text-muted-foreground space-y-1">
                <li>• Interactive orbit controls</li>
                <li>• Balanced multi-light setup</li>
                <li>• Ambient + directional + point lights</li>
                <li>• Theme-aware background</li>
                <li>• NVIDIA RTX 5090 3D model</li>
                <li>• Optimized texture visibility</li>
                <li>• Responsive canvas sizing</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
// Import OrbitControls from @tresjs/cientos
import { OrbitControls } from '@tresjs/cientos'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'

// Disable SSR for this page since TresJS is client-side only
definePageMeta({
  ssr: false
})

// Set page metadata
useHead({
  title: 'TresJS Testing - NIM Kit',
  meta: [
    { name: 'description', content: 'Interactive NVIDIA RTX 5090 3D model testing page using TresJS' }
  ]
})

// @ts-ignore - useColorMode is auto-imported by @nuxtjs/color-mode
const colorMode = useColorMode()

// Dynamic background color based on theme
const sceneBackgroundColor = computed(() => {
  return colorMode.value === 'dark' ? '#1a1a1a' : '#f8f9fa'
})

// Load the GLB model using useLoader
const config = useRuntimeConfig()
const gltfModel = await useLoader(GLTFLoader, `${config.public.apiBase}/models/nvidiaRTX5090.glb`)

// Extract the scene from the loaded model
const modelScene = computed(() => gltfModel.state.value?.scene)

// Debug: Log when component mounts
onMounted(() => {
  console.log('TresJS page mounted')
  console.log('GLTF Model:', gltfModel)
  console.log('Model Scene:', modelScene.value)
})
</script>
