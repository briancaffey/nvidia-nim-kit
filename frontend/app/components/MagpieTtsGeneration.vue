<template>
  <div>
    <!-- Not Configured State -->
    <Card v-if="!isConfigured">
      <CardHeader>
        <CardTitle class="flex items-center gap-2">
          <Icon name="lucide:settings" class="h-5 w-5" />
          NIM Not Configured
        </CardTitle>
        <CardDescription>
          This NIM needs to be configured before you can use it. Please configure the NIM with a host and port, or enable the NVIDIA API toggle to use the cloud API.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <p class="text-sm text-muted-foreground">
          Configure this NIM by clicking the "NIM Instance" button in the header, or toggle "Use NVIDIA API" in the settings to use the cloud-based API instead.
        </p>
      </CardContent>
    </Card>

    <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Left Side - Form -->
      <div class="space-y-6">
        <Card>
          <CardHeader>
            <div class="flex justify-between items-start">
              <div>
                <CardTitle>Text-to-Speech</CardTitle>
                <CardDescription>
                  Generate natural and expressive speech from text in multiple languages
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
            <!-- Language Selection -->
            <div class="space-y-2">
              <Label for="language">Language</Label>
              <Select v-model="formData.language" @update:modelValue="onLanguageChange">
                <SelectTrigger>
                  <SelectValue placeholder="Select language" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="lang in languages" :key="lang.code" :value="lang.code">
                    {{ lang.name }}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <!-- Voice Selection -->
            <div class="space-y-2">
              <Label for="voice">Voice</Label>
              <Select v-model="formData.voice" :disabled="filteredVoices.length === 0">
                <SelectTrigger>
                  <SelectValue :placeholder="voicesLoading ? 'Loading voices...' : 'Select voice'" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="voice in filteredVoices" :key="voice.name" :value="voice.name">
                    {{ voice.displayName }}
                  </SelectItem>
                </SelectContent>
              </Select>
              <p v-if="voicesError" class="text-sm text-red-500">{{ voicesError }}</p>
              <p v-else class="text-sm text-muted-foreground">
                {{ filteredVoices.length }} voice(s) available for {{ getLanguageName(formData.language) }}
              </p>
            </div>

            <!-- Sample Rate Selection -->
            <div class="space-y-2">
              <Label for="sampleRate">Sample Rate</Label>
              <Select v-model="formData.sampleRate">
                <SelectTrigger>
                  <SelectValue placeholder="Select sample rate" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="22050">22050 Hz (Default)</SelectItem>
                  <SelectItem value="44100">44100 Hz (High Quality)</SelectItem>
                  <SelectItem value="16000">16000 Hz</SelectItem>
                  <SelectItem value="8000">8000 Hz</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <!-- Text Input -->
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <Label for="text">Text to Synthesize</Label>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm" class="h-7 gap-1">
                      <Icon name="lucide:sparkles" class="h-3.5 w-3.5" />
                      Try a sample
                      <Icon name="lucide:chevron-down" class="h-3.5 w-3.5" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" class="w-80">
                    <DropdownMenuLabel>Sample sentences ({{ getLanguageName(formData.language) }})</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      v-for="(sentence, index) in currentLanguageSamples"
                      :key="index"
                      @click="formData.text = sentence"
                      class="cursor-pointer"
                    >
                      <span class="line-clamp-2 text-sm">{{ sentence }}</span>
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem @click="insertRandomSample" class="cursor-pointer">
                      <Icon name="lucide:shuffle" class="h-4 w-4 mr-2" />
                      Random sample
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
              <Textarea
                id="text"
                v-model="formData.text"
                placeholder="Enter the text you want to convert to speech..."
                class="min-h-[150px]"
              />
              <p class="text-sm text-muted-foreground">
                {{ formData.text.length }} characters
              </p>
            </div>

            <!-- Generate Button -->
            <Button
              @click="generateSpeech"
              :disabled="loading || !formData.text.trim()"
              class="w-full"
              size="lg"
            >
              <Icon v-if="loading" name="lucide:loader-2" class="h-4 w-4 mr-2 animate-spin" />
              <Icon v-else name="lucide:volume-2" class="h-4 w-4 mr-2" />
              {{ loading ? 'Generating...' : 'Generate Speech' }}
            </Button>

            <!-- Error Display -->
            <div v-if="error" class="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <div class="flex items-center">
                <Icon name="lucide:alert-circle" class="h-4 w-4 text-red-500 mr-2" />
                <p class="text-sm text-red-700 dark:text-red-300">{{ error }}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- Right Side - Results -->
      <div class="space-y-6">
        <Card v-if="ttsResult">
          <CardHeader>
            <CardTitle>Generated Audio</CardTitle>
            <CardDescription>
              Speech generated from your text
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <!-- Processing Info Badges -->
            <div class="mb-4">
              <div class="flex flex-wrap gap-2">
                <!-- Language Badge -->
                <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
                  {{ getLanguageName(ttsResult.output?.language) }}
                </span>

                <!-- Voice Badge -->
                <span v-if="ttsResult.output?.voice" class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                  {{ getVoiceDisplayName(ttsResult.output.voice) }}
                </span>

                <!-- Sample Rate Badge -->
                <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                  {{ ttsResult.output?.sample_rate_hz || 22050 }} Hz
                </span>

                <!-- File Size Badge -->
                <span v-if="ttsResult.output?.audio_size_bytes" class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200">
                  {{ formatFileSize(ttsResult.output.audio_size_bytes) }}
                </span>
              </div>
            </div>

            <!-- Audio Player -->
            <div>
              <Label class="text-sm font-medium">Audio Playback</Label>
              <div class="mt-2 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <audio
                  v-if="ttsResult.output?.audio_path"
                  :src="getAudioUrl(ttsResult.output.audio_path)"
                  controls
                  class="w-full"
                >
                  Your browser does not support the audio element.
                </audio>
                <p v-else class="text-sm text-gray-500">No audio available</p>
              </div>
            </div>

            <!-- Synthesized Text -->
            <div>
              <Label class="text-sm font-medium">Synthesized Text</Label>
              <div class="mt-2 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm">
                {{ ttsResult.output?.text }}
              </div>
            </div>

            <!-- Download Button -->
            <div v-if="ttsResult.output?.audio_path">
              <Button
                @click="downloadAudio"
                variant="outline"
                class="w-full"
              >
                <Icon name="lucide:download" class="h-4 w-4 mr-2" />
                Download Audio
              </Button>
            </div>
          </CardContent>
        </Card>

        <!-- Request Info Card -->
        <Card v-if="ttsResult">
          <CardHeader>
            <CardTitle>Request Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-gray-500">Request ID:</span>
                <span class="font-mono text-xs">{{ ttsResult.request_id || 'N/A' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">Status:</span>
                <span class="capitalize">{{ ttsResult.status || 'N/A' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">Date Created:</span>
                <span>{{ formatDate(ttsResult.date_created) }}</span>
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
          <div v-if="ttsResult">
            <Label class="text-sm font-medium">Response Data</Label>
            <pre class="mt-2 p-4 bg-gray-100 dark:bg-gray-800 rounded-lg text-xs overflow-auto max-h-64">{{ JSON.stringify(ttsResult, null, 2) }}</pre>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useNvidiaApiToggle } from '@/composables/useNvidiaApiToggle'

interface Voice {
  name: string
  displayName: string
  language: string
  emotion?: string
}

interface NimConfig {
  host: string
  port: number
  nim_type?: string
}

// Props
const props = defineProps<{
  nimId: string
  nimConfig?: NimConfig | null
}>()

// Runtime config
const config = useRuntimeConfig()

// NVIDIA API toggle
const { useNvidiaApi } = useNvidiaApiToggle()

// Computed: check if NIM is configured (either locally or using NVIDIA API)
const isConfigured = computed(() => {
  return !!props.nimConfig || useNvidiaApi.value
})

// Available languages
const languages = [
  { code: 'en-US', name: 'English (US)' },
  { code: 'es-US', name: 'Spanish (US)' },
  { code: 'fr-FR', name: 'French (France)' },
  { code: 'de-DE', name: 'German (Germany)' },
  { code: 'zh-CN', name: 'Chinese (Simplified)' },
  { code: 'vi-VN', name: 'Vietnamese' },
  { code: 'it-IT', name: 'Italian' },
]

// Sample sentences for each language
const sampleSentences: Record<string, string[]> = {
  'en-US': [
    'The quick brown fox jumps over the lazy dog.',
    'Welcome to our text-to-speech demonstration. We hope you enjoy the natural sound of our voices.',
    'In a world of artificial intelligence, the ability to communicate naturally has never been more important.',
    'The weather today is absolutely beautiful, with clear skies and a gentle breeze.',
    'Please remember to subscribe to our newsletter for the latest updates and announcements.',
  ],
  'es-US': [
    'El veloz zorro marrón salta sobre el perro perezoso.',
    'Bienvenidos a nuestra demostración de texto a voz. Esperamos que disfruten del sonido natural de nuestras voces.',
    'En un mundo de inteligencia artificial, la capacidad de comunicarse naturalmente nunca ha sido más importante.',
    'El clima hoy está absolutamente hermoso, con cielos despejados y una brisa suave.',
    'Por favor recuerde suscribirse a nuestro boletín para las últimas actualizaciones y anuncios.',
  ],
  'fr-FR': [
    'Le rapide renard brun saute par-dessus le chien paresseux.',
    'Bienvenue à notre démonstration de synthèse vocale. Nous espérons que vous apprécierez le son naturel de nos voix.',
    'Dans un monde d\'intelligence artificielle, la capacité de communiquer naturellement n\'a jamais été aussi importante.',
    'Le temps aujourd\'hui est absolument magnifique, avec un ciel dégagé et une brise légère.',
    'N\'oubliez pas de vous abonner à notre newsletter pour les dernières mises à jour et annonces.',
  ],
  'de-DE': [
    'Der schnelle braune Fuchs springt über den faulen Hund.',
    'Willkommen zu unserer Text-zu-Sprache-Demonstration. Wir hoffen, dass Ihnen der natürliche Klang unserer Stimmen gefällt.',
    'In einer Welt der künstlichen Intelligenz war die Fähigkeit zur natürlichen Kommunikation noch nie so wichtig.',
    'Das Wetter heute ist absolut wunderschön, mit klarem Himmel und einer sanften Brise.',
    'Bitte denken Sie daran, unseren Newsletter zu abonnieren, um die neuesten Updates und Ankündigungen zu erhalten.',
  ],
  'zh-CN': [
    '快速的棕色狐狸跳过了懒狗。',
    '欢迎来到我们的文字转语音演示。我们希望您能喜欢我们声音的自然效果。',
    '在人工智能的世界里，自然沟通的能力从未如此重要。',
    '今天的天气非常好，天空晴朗，微风习习。',
    '请记得订阅我们的通讯，以获取最新的更新和公告。',
  ],
  'vi-VN': [
    'Con cáo nâu nhanh nhẹn nhảy qua con chó lười.',
    'Chào mừng đến với bản trình diễn chuyển văn bản thành giọng nói của chúng tôi. Chúng tôi hy vọng bạn sẽ thích âm thanh tự nhiên của giọng nói.',
    'Trong thế giới trí tuệ nhân tạo, khả năng giao tiếp tự nhiên chưa bao giờ quan trọng hơn thế.',
    'Thời tiết hôm nay thật tuyệt vời, với bầu trời trong xanh và gió nhẹ.',
    'Vui lòng nhớ đăng ký nhận bản tin của chúng tôi để cập nhật thông tin và thông báo mới nhất.',
  ],
  'it-IT': [
    'La veloce volpe marrone salta sopra il cane pigro.',
    'Benvenuti alla nostra dimostrazione di sintesi vocale. Speriamo che apprezzerete il suono naturale delle nostre voci.',
    'In un mondo di intelligenza artificiale, la capacità di comunicare naturalmente non è mai stata così importante.',
    'Il tempo oggi è assolutamente bellissimo, con cieli sereni e una leggera brezza.',
    'Ricordatevi di iscrivervi alla nostra newsletter per gli ultimi aggiornamenti e annunci.',
  ],
}

// Reactive data
const formData = reactive({
  language: 'en-US',
  voice: '',
  sampleRate: '22050',
  text: ''
})

const allVoices = ref<Voice[]>([])
const voicesLoading = ref(false)
const voicesError = ref('')
const loading = ref(false)
const error = ref('')
const ttsResult = ref<any>(null)
const showJsonModal = ref(false)

// Computed: filtered voices based on selected language
const filteredVoices = computed(() => {
  const langCode = formData.language.toUpperCase().replace('-', '.')
  const langPrefix = formData.language.split('-')[0].toUpperCase()

  return allVoices.value.filter(voice => {
    // Match voices that contain the language code
    const voiceLangMatch = voice.name.includes(langCode) ||
                          voice.name.includes(langPrefix + '-') ||
                          voice.name.includes('.' + langPrefix + '.')

    return voiceLangMatch
  })
})

// Computed: sample sentences for current language
const currentLanguageSamples = computed(() => {
  return sampleSentences[formData.language] || sampleSentences['en-US']
})

// Methods
const insertRandomSample = () => {
  const samples = currentLanguageSamples.value
  const randomIndex = Math.floor(Math.random() * samples.length)
  formData.text = samples[randomIndex]
}
const getLanguageName = (code: string) => {
  const lang = languages.find(l => l.code === code)
  return lang ? lang.name : code
}

const getVoiceDisplayName = (voiceName: string) => {
  // Extract just the voice name from the full name
  // e.g., "Magpie-Multilingual.EN-US.Aria" -> "Aria"
  const parts = voiceName.split('.')
  return parts[parts.length - 1] || voiceName
}

const parseVoiceName = (fullName: string): Voice => {
  // Parse voice names like "Magpie-Multilingual.EN-US.Aria" or "Magpie-Multilingual.EN-US.Aria.Neutral"
  const parts = fullName.split('.')
  let voiceName = parts[parts.length - 1]
  let emotion = ''

  // Check if last part is an emotion
  const emotions = ['Neutral', 'Calm', 'Angry', 'Happy', 'Sad', 'Fearful', 'Disgust', 'PleasantSurprise']
  if (emotions.includes(voiceName) && parts.length > 3) {
    emotion = voiceName
    voiceName = parts[parts.length - 2]
  }

  const displayName = emotion ? `${voiceName} (${emotion})` : voiceName

  return {
    name: fullName,
    displayName,
    language: parts.length > 1 ? parts[1] : '',
    emotion
  }
}

const fetchVoices = async () => {
  voicesLoading.value = true
  voicesError.value = ''

  try {
    const response = await fetch(
      `${config.public.apiBase}/v0/tts/${props.nimId}/voices?use_nvidia_api=${useNvidiaApi.value}`
    )

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Failed to fetch voices')
    }

    const data = await response.json()

    // Parse the voices list
    // The API returns {"voices": ["voice1", "voice2", ...]}
    if (data.voices && Array.isArray(data.voices)) {
      allVoices.value = data.voices.map((name: string) => parseVoiceName(name))
    } else {
      allVoices.value = []
    }

    // Set default voice if available
    if (filteredVoices.value.length > 0 && !formData.voice) {
      formData.voice = filteredVoices.value[0].name
    }
  } catch (err) {
    console.error('Error fetching voices:', err)
    voicesError.value = err instanceof Error ? err.message : 'Failed to fetch voices'
  } finally {
    voicesLoading.value = false
  }
}

const onLanguageChange = () => {
  // Reset voice selection when language changes
  formData.voice = ''

  // Set first available voice for new language
  if (filteredVoices.value.length > 0) {
    formData.voice = filteredVoices.value[0].name
  }
}

const generateSpeech = async () => {
  if (!formData.text.trim()) {
    error.value = 'Please enter text to synthesize'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const formDataToSend = new FormData()
    formDataToSend.append('text', formData.text)
    formDataToSend.append('language', formData.language)
    formDataToSend.append('sample_rate_hz', formData.sampleRate)

    if (formData.voice) {
      formDataToSend.append('voice', formData.voice)
    }

    const response = await fetch(
      `${config.public.apiBase}/v0/tts/${props.nimId}?use_nvidia_api=${useNvidiaApi.value}`,
      {
        method: 'POST',
        body: formDataToSend
      }
    )

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Failed to generate speech')
    }

    const result = await response.json()
    ttsResult.value = result
  } catch (err) {
    console.error('Error generating speech:', err)
    error.value = err instanceof Error ? err.message : 'Failed to generate speech'
  } finally {
    loading.value = false
  }
}

const downloadAudio = () => {
  if (ttsResult.value?.output?.audio_path) {
    const link = document.createElement('a')
    link.href = getAudioUrl(ttsResult.value.output.audio_path)
    link.download = `tts_audio_${Date.now()}.wav`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }
}

const getAudioUrl = (audioPath: string) => {
  // Convert the file path to a URL that can be accessed by the frontend
  const fileName = audioPath.split('/').pop()
  return `${config.public.apiBase}/media/tts/output/${fileName}`
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (dateString: string) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString()
}

// Lifecycle
onMounted(() => {
  if (isConfigured.value) {
    fetchVoices()
  }
})

// Watch for configuration changes
watch(isConfigured, (newValue) => {
  if (newValue && allVoices.value.length === 0) {
    fetchVoices()
  }
})
</script>
