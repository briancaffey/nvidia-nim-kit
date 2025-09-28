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
            <!-- Mode Selection -->
            <div class="space-y-2">
              <Label for="mode">Mode</Label>
              <Select v-model="formData.mode">
                <SelectTrigger>
                  <SelectValue placeholder="Select mode" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="offline">Offline</SelectItem>
                </SelectContent>
              </Select>
              <p class="text-sm text-muted-foreground">
                Currently only offline mode is supported
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

            <!-- Transcribe Button -->
            <Button
              @click="transcribeAudio"
              :disabled="loading || (!uploadedFile && !recordedAudio)"
              class="w-full"
              size="lg"
            >
              <Icon v-if="loading" name="lucide:loader-2" class="h-4 w-4 mr-2 animate-spin" />
              <Icon v-else name="lucide:mic" class="h-4 w-4 mr-2" />
              {{ loading ? 'Transcribing...' : 'Transcribe Audio' }}
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
        <Card v-if="asrResult">
          <CardHeader>
            <CardTitle>Transcription Results</CardTitle>
            <CardDescription>
              Speech-to-text output with timestamps
            </CardDescription>
          </CardHeader>
          <CardContent>
            <!-- Full Text -->
            <div class="space-y-4">
              <div>
                <Label class="text-sm font-medium">Transcribed Text</Label>
                <div class="mt-2 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <p class="text-sm text-gray-900 dark:text-gray-100">{{ asrResult.text || 'No text transcribed' }}</p>
                </div>
              </div>

              <!-- Word-level Timestamps -->
              <div v-if="asrResult.words && asrResult.words.length > 0">
                <Label class="text-sm font-medium">Word-level Timestamps</Label>
                <div class="mt-2">
                  <WordTimestamps
                    :words="asrResult.words"
                    :audio-url="getAudioUrl()"
                  />
                </div>
              </div>

              <!-- Confidence Score -->
              <div v-if="asrResult.confidence !== undefined">
                <Label class="text-sm font-medium">Confidence Score</Label>
                <div class="mt-2">
                  <div class="flex items-center space-x-2">
                    <div class="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        class="bg-green-500 h-2 rounded-full"
                        :style="{ width: `${asrResult.confidence * 100}%` }"
                      ></div>
                    </div>
                    <span class="text-sm text-gray-600 dark:text-gray-300">
                      {{ Math.round(asrResult.confidence * 100) }}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Placeholder when no results -->
        <Card v-else>
          <CardContent class="flex items-center justify-center h-64">
            <div class="text-center text-gray-500">
              <Icon name="lucide:mic" class="h-12 w-12 mx-auto mb-4" />
              <p>Upload or record audio to see transcription results</p>
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
            <pre class="mt-2 p-4 bg-gray-100 rounded-lg text-sm overflow-auto max-h-64">{{ JSON.stringify(getPayloadForDisplay(), null, 2) }}</pre>
          </div>
          <div v-if="inferenceResult">
            <Label class="text-sm font-medium">Response Data</Label>
            <pre class="mt-2 p-4 bg-gray-100 rounded-lg text-sm overflow-auto max-h-64">{{ JSON.stringify(inferenceResult, null, 2) }}</pre>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import WordTimestamps from '@/components/WordTimestamps.vue'

interface Props {
  nimId: string
}

const props = defineProps<Props>()

interface FormData {
  mode: string
}

interface AsrResult {
  text?: string
  words?: Array<{
    word: string
    start_time: number
    end_time: number
    confidence?: number
  }>
  confidence?: number
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
  output?: AsrResult
  error?: any
  nim_metadata: any
  nim_config: any
}

const config = useRuntimeConfig()

// Form data
const formData = ref<FormData>({
  mode: 'offline'
})

// State
const loading = ref(false)
const error = ref<string | null>(null)
const asrResult = ref<AsrResult | null>(null)
const inferenceResult = ref<InferenceResult | null>(null)
const showJsonModal = ref(false)

// Audio input method
const inputMethod = ref<'upload' | 'record'>('upload')

// File upload state
const uploadedFile = ref<File | null>(null)

// Audio recording state
const isRecording = ref(false)
const recordedAudio = ref<Blob | null>(null)
const recordingDuration = ref(0)
const microphonePermission = ref(false)
const mediaRecorder = ref<MediaRecorder | null>(null)
const recordingInterval = ref<NodeJS.Timeout | null>(null)

// Use NIM ID from props
const nimId = computed(() => props.nimId)

const getPayloadForDisplay = () => {
  return {
    mode: formData.value.mode,
    audio_file: uploadedFile.value ? uploadedFile.value.name : 'recorded_audio',
    input_method: inputMethod.value
  }
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDuration = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const formatTimestamp = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  const ms = Math.floor((seconds % 1) * 1000)
  return `${mins}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`
}

const getAudioUrl = (): string | undefined => {
  if (uploadedFile.value) {
    return URL.createObjectURL(uploadedFile.value)
  } else if (recordedAudio.value) {
    return URL.createObjectURL(recordedAudio.value)
  }
  return undefined
}

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    uploadedFile.value = file
    clearRecording() // Clear any existing recording
  }
}

const clearUploadedFile = () => {
  uploadedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const fileInput = ref<HTMLInputElement | null>(null)

const checkMicrophonePermission = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    microphonePermission.value = true
    stream.getTracks().forEach(track => track.stop()) // Stop the stream immediately
  } catch (error) {
    console.error('Microphone permission denied:', error)
    microphonePermission.value = false
  }
}

const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder.value = new MediaRecorder(stream, { mimeType: 'audio/webm' })
    const audioChunks: BlobPart[] = []

    mediaRecorder.value.ondataavailable = (event) => {
      audioChunks.push(event.data)
    }

    mediaRecorder.value.onstop = () => {
      // Create a blob with the recorded audio
      const recordedBlob = new Blob(audioChunks, { type: 'audio/webm' })

      // Convert to WAV format for RIVA compatibility
      convertToWav(recordedBlob).then((wavBlob) => {
        recordedAudio.value = wavBlob
        stream.getTracks().forEach(track => track.stop())
      }).catch((error) => {
        console.error('Error converting to WAV:', error)
        error.value = 'Failed to process recorded audio'
        stream.getTracks().forEach(track => track.stop())
      })
    }

    mediaRecorder.value.start()
    isRecording.value = true
    recordingDuration.value = 0
    clearUploadedFile() // Clear any uploaded file

    // Start duration timer
    recordingInterval.value = setInterval(() => {
      recordingDuration.value += 0.1
    }, 100)

  } catch (error) {
    console.error('Error starting recording:', error)
    error.value = 'Failed to start recording. Please check microphone permissions.'
  }
}

const convertToWav = async (webmBlob: Blob): Promise<Blob> => {
  return new Promise((resolve, reject) => {
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
    const fileReader = new FileReader()

    fileReader.onload = async () => {
      try {
        const arrayBuffer = fileReader.result as ArrayBuffer
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)

        // Convert to WAV format
        const wavBuffer = audioBufferToWav(audioBuffer)
        const wavBlob = new Blob([wavBuffer], { type: 'audio/wav' })
        resolve(wavBlob)
      } catch (error) {
        reject(error)
      }
    }

    fileReader.onerror = reject
    fileReader.readAsArrayBuffer(webmBlob)
  })
}

const audioBufferToWav = (audioBuffer: AudioBuffer): ArrayBuffer => {
  const numberOfChannels = 1 // Force mono
  const sampleRate = audioBuffer.sampleRate
  const length = audioBuffer.length

  // Create a mono buffer by averaging stereo channels if needed
  const monoBuffer = new Float32Array(length)
  if (audioBuffer.numberOfChannels === 1) {
    monoBuffer.set(audioBuffer.getChannelData(0))
  } else {
    // Average multiple channels to mono
    const channelData = []
    for (let i = 0; i < audioBuffer.numberOfChannels; i++) {
      channelData.push(audioBuffer.getChannelData(i))
    }
    for (let i = 0; i < length; i++) {
      let sum = 0
      for (let j = 0; j < channelData.length; j++) {
        sum += channelData[j][i]
      }
      monoBuffer[i] = sum / channelData.length
    }
  }

  // Convert to 16-bit PCM
  const buffer = new ArrayBuffer(44 + length * 2)
  const view = new DataView(buffer)

  // WAV header
  const writeString = (offset: number, string: string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i))
    }
  }

  writeString(0, 'RIFF')
  view.setUint32(4, 36 + length * 2, true)
  writeString(8, 'WAVE')
  writeString(12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, numberOfChannels, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * numberOfChannels * 2, true)
  view.setUint16(32, numberOfChannels * 2, true)
  view.setUint16(34, 16, true)
  writeString(36, 'data')
  view.setUint32(40, length * 2, true)

  // Convert float samples to 16-bit PCM
  let offset = 44
  for (let i = 0; i < length; i++) {
    const sample = Math.max(-1, Math.min(1, monoBuffer[i]))
    view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true)
    offset += 2
  }

  return buffer
}

const stopRecording = () => {
  if (mediaRecorder.value && isRecording.value) {
    mediaRecorder.value.stop()
    isRecording.value = false
    if (recordingInterval.value) {
      clearInterval(recordingInterval.value)
      recordingInterval.value = null
    }
  }
}

const clearRecording = () => {
  recordedAudio.value = null
  recordingDuration.value = 0
  if (recordingInterval.value) {
    clearInterval(recordingInterval.value)
    recordingInterval.value = null
  }
}

const playRecording = () => {
  if (recordedAudio.value) {
    const audioUrl = URL.createObjectURL(recordedAudio.value)
    const audio = new Audio(audioUrl)
    audio.play()
  }
}

const transcribeAudio = async () => {
  if (!uploadedFile.value && !recordedAudio.value) {
    error.value = 'Please upload a file or record audio first'
    return
  }

  try {
    loading.value = true
    error.value = null
    asrResult.value = null
    inferenceResult.value = null

    console.log('Starting ASR transcription...')

    const toggleResponse = await fetch(`${config.public.apiBase}/api/nvidia/toggle`)
    const toggleData = await toggleResponse.json()
    const useNvidiaApi = toggleData.enabled

    // Prepare form data
    const formDataToSend = new FormData()
    formDataToSend.append('mode', formData.value.mode)

    if (uploadedFile.value) {
      formDataToSend.append('audio_file', uploadedFile.value)
    } else if (recordedAudio.value) {
      // Convert recorded audio to file
      const audioFile = new File([recordedAudio.value], 'recorded_audio.wav', {
        type: 'audio/wav'
      })
      formDataToSend.append('audio_file', audioFile)
    }

    const response = await $fetch<InferenceResult>(`${config.public.apiBase}/v0/asr/${nimId.value}?use_nvidia_api=${useNvidiaApi}`, {
      method: 'POST',
      body: formDataToSend
    })

    console.log('ASR response:', response)
    inferenceResult.value = response

    // Extract ASR results from response
    if (response.output) {
      asrResult.value = response.output
    }

  } catch (err: any) {
    console.error('ASR transcription failed:', err)
    error.value = err.data?.detail || err.message || 'ASR transcription failed'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  checkMicrophonePermission()
})

onUnmounted(() => {
  if (recordingInterval.value) {
    clearInterval(recordingInterval.value)
  }
  if (mediaRecorder.value && isRecording.value) {
    mediaRecorder.value.stop()
  }
})

// Set page metadata
useHead({
  title: 'RIVA ASR Generation - NIM Kit',
  meta: [
    {
      name: 'description',
      content: 'Transcribe audio files using NVIDIA RIVA ASR with automatic speech recognition'
    }
  ]
})
</script>
