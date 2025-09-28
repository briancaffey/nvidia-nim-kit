<template>
  <div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Left Side - Form -->
      <div class="space-y-6">
        <Card>
          <CardHeader>
            <div class="flex justify-between items-start">
              <div>
                <CardTitle>Audio Input</CardTitle>
                <CardDescription>
                  Upload an audio file or record audio using your microphone
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
            <!-- Model Type Selection -->
            <div class="space-y-2">
              <Label for="modelType">Model Type</Label>
              <Select v-model="formData.modelType">
                <SelectTrigger>
                  <SelectValue placeholder="Select model type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="48k-hq">48k-hq (High Quality)</SelectItem>
                  <SelectItem value="48k-ll">48k-ll (Low Latency)</SelectItem>
                  <SelectItem value="16k-hq">16k-hq (16kHz High Quality)</SelectItem>
                </SelectContent>
              </Select>
              <p class="text-sm text-muted-foreground">
                Choose the Studio Voice model type based on your needs
              </p>
            </div>

            <!-- Audio Input Method Selection -->
            <div class="space-y-2">
              <Label>Audio Input Method</Label>
              <div class="flex gap-2">
                <Button
                  :variant="inputMethod === 'upload' ? 'default' : 'outline'"
                  @click="inputMethod = 'upload'"
                  class="flex items-center gap-2"
                >
                  <Icon name="lucide:upload" class="h-4 w-4" />
                  Upload File
                </Button>
                <Button
                  :variant="inputMethod === 'record' ? 'default' : 'outline'"
                  @click="inputMethod = 'record'"
                  class="flex items-center gap-2"
                >
                  <Icon name="lucide:mic" class="h-4 w-4" />
                  Record Audio
                </Button>
              </div>
            </div>

            <!-- File Upload Section -->
            <div v-if="inputMethod === 'upload'" class="space-y-4">
              <div class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <input
                  ref="fileInput"
                  type="file"
                  accept="audio/*"
                  @change="handleFileUpload"
                  class="hidden"
                />
                <div v-if="!uploadedFile" class="space-y-2">
                  <Icon name="lucide:upload" class="h-8 w-8 mx-auto text-gray-400" />
                  <p class="text-sm text-gray-600">Click to upload audio file</p>
                  <Button @click="$refs.fileInput.click()" variant="outline">
                    Choose File
                  </Button>
                </div>
                <div v-else class="space-y-2">
                  <Icon name="lucide:file-audio" class="h-8 w-8 mx-auto text-green-500" />
                  <p class="text-sm font-medium">{{ uploadedFile.name }}</p>
                  <p class="text-xs text-gray-500">{{ formatFileSize(uploadedFile.size) }}</p>
                  <Button @click="clearUploadedFile" variant="outline" size="sm">
                    Remove File
                  </Button>
                </div>
              </div>
            </div>

            <!-- Audio Recording Section -->
            <div v-if="inputMethod === 'record'" class="space-y-4">
              <div class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <div v-if="!isRecording && !recordedAudio" class="space-y-2">
                  <Icon name="lucide:mic" class="h-8 w-8 mx-auto text-gray-400" />
                  <p class="text-sm text-gray-600">Click to start recording</p>
                  <Button
                    @click="startRecording"
                    :disabled="!microphonePermission"
                    variant="outline"
                  >
                    <Icon name="lucide:mic" class="h-4 w-4 mr-2" />
                    Start Recording
                  </Button>
                  <p v-if="!microphonePermission" class="text-xs text-red-500">
                    Microphone permission required
                  </p>
                </div>

                <div v-if="isRecording" class="space-y-2">
                  <div class="flex items-center justify-center space-x-2">
                    <div class="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                    <p class="text-sm font-medium">Recording...</p>
                  </div>
                  <p class="text-xs text-gray-500">{{ formatDuration(recordingDuration) }}</p>
                  <Button @click="stopRecording" variant="destructive">
                    <Icon name="lucide:square" class="h-4 w-4 mr-2" />
                    Stop Recording
                  </Button>
                </div>

                <div v-if="recordedAudio && !isRecording" class="space-y-2">
                  <Icon name="lucide:file-audio" class="h-8 w-8 mx-auto text-green-500" />
                  <p class="text-sm font-medium">Recording Complete</p>
                  <p class="text-xs text-gray-500">{{ formatDuration(recordingDuration) }}</p>
                  <div class="flex gap-2 justify-center">
                    <Button @click="playRecording" variant="outline" size="sm">
                      <Icon name="lucide:play" class="h-4 w-4 mr-1" />
                      Play
                    </Button>
                    <Button @click="clearRecording" variant="outline" size="sm">
                      <Icon name="lucide:trash" class="h-4 w-4 mr-1" />
                      Delete
                    </Button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Enhance Button -->
            <Button
              @click="enhanceAudio"
              :disabled="loading || (!uploadedFile && !recordedAudio)"
              class="w-full"
              size="lg"
            >
              <Icon v-if="loading" name="lucide:loader-2" class="h-4 w-4 mr-2 animate-spin" />
              <Icon v-else name="lucide:volume-2" class="h-4 w-4 mr-2" />
              {{ loading ? 'Enhancing...' : 'Enhance Audio' }}
            </Button>

            <!-- Error Display -->
            <div v-if="error" class="p-4 bg-red-50 border border-red-200 rounded-lg">
              <div class="flex items-center">
                <Icon name="lucide:alert-circle" class="h-4 w-4 text-red-500 mr-2" />
                <p class="text-sm text-red-700">{{ error }}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- Right Side - Results -->
      <div class="space-y-6">
        <Card v-if="enhancementResult">
          <CardHeader>
            <CardTitle>Enhancement Results</CardTitle>
            <CardDescription>
              Enhanced audio with improved quality and noise reduction
            </CardDescription>
          </CardHeader>
          <CardContent>
            <!-- Processing Info Badges -->
            <div class="mb-4">
              <div class="flex flex-wrap gap-2">
                <!-- Model Type Badge -->
                <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
                  {{ enhancementResult.output?.model_type || 'N/A' }}
                </span>

                <!-- API Type Badge -->
                <span v-if="enhancementResult.output?.api_type === 'nvidia_cloud'" class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                  NVIDIA Cloud
                </span>
                <span v-else-if="enhancementResult.output?.api_type === 'local_nim'" class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                  Local NIM
                </span>

                <!-- Processing Time Badge -->
                <span v-if="enhancementResult.output?.processing_time_seconds" class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200">
                  {{ enhancementResult.output.processing_time_seconds.toFixed(2) }}s
                </span>

                <!-- Sample Rate Badge -->
                <span v-if="enhancementResult.output?.sample_rate" class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200">
                  {{ enhancementResult.output.sample_rate }} Hz
                </span>
              </div>
            </div>

            <!-- Audio Player -->
            <div>
                <Label class="text-sm font-medium">Enhanced Audio</Label>
                <div class="mt-2 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <audio
                    v-if="enhancementResult.output?.enhanced_audio_path"
                    :src="getAudioUrl(enhancementResult.output.enhanced_audio_path)"
                    controls
                    class="w-full"
                  >
                    Your browser does not support the audio element.
                  </audio>
                  <p v-else class="text-sm text-gray-500">No enhanced audio available</p>
                </div>
              </div>

              <!-- Original Audio Player -->
              <div>
                <Label class="text-sm font-medium">Original Audio</Label>
                <div class="mt-2 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <audio
                    v-if="enhancementResult.output?.input_file"
                    :src="getOriginalAudioUrl(enhancementResult.output.input_file)"
                    controls
                    class="w-full"
                  >
                    Your browser does not support the audio element.
                  </audio>
                  <p v-else class="text-sm text-gray-500">No original audio available</p>
                </div>
              </div>

              <!-- Download Button -->
              <div v-if="enhancementResult.output?.enhanced_audio_path">
                <Button
                  @click="downloadEnhancedAudio"
                  variant="outline"
                  class="w-full"
                >
                  <Icon name="lucide:download" class="h-4 w-4 mr-2" />
                  Download Enhanced Audio
                </Button>
              </div>
          </CardContent>
        </Card>

        <!-- Request Info Card -->
        <Card v-if="enhancementResult">
          <CardHeader>
            <CardTitle>Request Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-gray-500">Request ID:</span>
                <span class="font-mono">{{ enhancementResult.request_id || 'N/A' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">Status:</span>
                <span class="capitalize">{{ enhancementResult.status || 'N/A' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">Date Created:</span>
                <span>{{ formatDate(enhancementResult.date_created) }}</span>
              </div>
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
            <Label class="text-sm font-medium">Request Data</Label>
            <pre class="mt-2 p-4 bg-gray-100 dark:bg-gray-800 rounded-lg text-xs overflow-auto max-h-64">{{ JSON.stringify(formData, null, 2) }}</pre>
          </div>
          <div v-if="enhancementResult">
            <Label class="text-sm font-medium">Response Data</Label>
            <pre class="mt-2 p-4 bg-gray-100 dark:bg-gray-800 rounded-lg text-xs overflow-auto max-h-64">{{ JSON.stringify(enhancementResult, null, 2) }}</pre>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useNvidiaApiToggle } from '@/composables/useNvidiaApiToggle'

// Props
const props = defineProps<{
  nimId: string
}>()

// Runtime config
const config = useRuntimeConfig()

// NVIDIA API toggle
const { useNvidiaApi } = useNvidiaApiToggle()

// Reactive data
const formData = reactive({
  modelType: '48k-hq'
})

const inputMethod = ref<'upload' | 'record'>('upload')
const uploadedFile = ref<File | null>(null)
const recordedAudio = ref<Blob | null>(null)
const isRecording = ref(false)
const recordingDuration = ref(0)
const microphonePermission = ref(false)
const loading = ref(false)
const error = ref('')
const enhancementResult = ref<any>(null)
const showJsonModal = ref(false)

// MediaRecorder and related variables
let mediaRecorder: MediaRecorder | null = null
let recordingChunks: Blob[] = []
let recordingTimer: number | null = null

// Methods
const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    uploadedFile.value = file
    error.value = ''
  }
}

const clearUploadedFile = () => {
  uploadedFile.value = null
  const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
  if (fileInput) {
    fileInput.value = ''
  }
}

const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder = new MediaRecorder(stream)
    recordingChunks = []

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        recordingChunks.push(event.data)
      }
    }

    mediaRecorder.onstop = () => {
      recordedAudio.value = new Blob(recordingChunks, { type: 'audio/wav' })
      stream.getTracks().forEach(track => track.stop())
    }

    mediaRecorder.start()
    isRecording.value = true
    recordingDuration.value = 0

    recordingTimer = setInterval(() => {
      recordingDuration.value++
    }, 1000)

    error.value = ''
  } catch (err) {
    console.error('Error starting recording:', err)
    error.value = 'Failed to start recording. Please check microphone permissions.'
  }
}

const stopRecording = () => {
  if (mediaRecorder && isRecording.value) {
    mediaRecorder.stop()
    isRecording.value = false
    if (recordingTimer) {
      clearInterval(recordingTimer)
      recordingTimer = null
    }
  }
}

const playRecording = () => {
  if (recordedAudio.value) {
    const audio = new Audio(URL.createObjectURL(recordedAudio.value))
    audio.play()
  }
}

const clearRecording = () => {
  recordedAudio.value = null
  recordingDuration.value = 0
}

const enhanceAudio = async () => {
  if (!uploadedFile.value && !recordedAudio.value) {
    error.value = 'Please upload a file or record audio first'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const formDataToSend = new FormData()
    formDataToSend.append('model_type', formData.modelType)

    if (uploadedFile.value) {
      formDataToSend.append('audio_file', uploadedFile.value)
    } else if (recordedAudio.value) {
      const audioFile = new File([recordedAudio.value], 'recording.wav', { type: 'audio/wav' })
      formDataToSend.append('audio_file', audioFile)
    }

    const response = await fetch(`${config.public.apiBase}/v0/speech-enhancement/${props.nimId}?use_nvidia_api=${useNvidiaApi.value}`, {
      method: 'POST',
      body: formDataToSend
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Failed to enhance audio')
    }

    const result = await response.json()
    enhancementResult.value = result
  } catch (err) {
    console.error('Error enhancing audio:', err)
    error.value = err instanceof Error ? err.message : 'Failed to enhance audio'
  } finally {
    loading.value = false
  }
}

const downloadEnhancedAudio = () => {
  if (enhancementResult.value?.output?.enhanced_audio_path) {
    const link = document.createElement('a')
    link.href = getAudioUrl(enhancementResult.value.output.enhanced_audio_path)
    link.download = `enhanced_audio_${Date.now()}.wav`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }
}

const getAudioUrl = (audioPath: string) => {
  // Convert the file path to a URL that can be accessed by the frontend
  const fileName = audioPath.split('/').pop()
  return `${config.public.apiBase}/media/studiovoice/output/${fileName}`
}

const getOriginalAudioUrl = (audioPath: string) => {
  // Convert the file path to a URL that can be accessed by the frontend
  const fileName = audioPath.split('/').pop()
  return `${config.public.apiBase}/media/studiovoice/input/${fileName}`
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDuration = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}

// Lifecycle
onMounted(async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    microphonePermission.value = true
    stream.getTracks().forEach(track => track.stop())
  } catch (err) {
    console.error('Microphone permission denied:', err)
    microphonePermission.value = false
  }
})

onUnmounted(() => {
  if (recordingTimer) {
    clearInterval(recordingTimer)
  }
  if (mediaRecorder && isRecording.value) {
    mediaRecorder.stop()
  }
})
</script>
