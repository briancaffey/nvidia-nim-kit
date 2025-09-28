<template>
  <Card>
    <CardHeader>
      <CardTitle class="flex items-center gap-2">
        <Icon name="lucide:plus" class="h-5 w-5" />
        {{ title || 'Add New NIM' }}
      </CardTitle>
      <CardDescription>
        {{ description || 'Configure a new NVIDIA Inference Microservice' }}
      </CardDescription>
    </CardHeader>
    <CardContent>
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <Label for="nim-id">NIM ID</Label>
          <Input
            id="nim-id"
            v-model="formData.nim_id"
            placeholder="e.g., meta/llama-3_1-8b-instruct"
            :disabled="nimIdDisabled"
            required
            class="mt-1"
          />
          <p class="text-sm text-muted-foreground mt-1">
            {{ nimIdDisabled ? 'NIM ID is pre-filled for this NIM' : 'Unique identifier for the NIM' }}
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label for="host">Host Address</Label>
            <Input
              id="host"
              v-model="formData.host"
              placeholder="e.g., localhost or 192.168.1.100"
              required
              class="mt-1"
            />
          </div>
          <div>
            <Label for="port">Port Number</Label>
            <Input
              id="port"
              v-model.number="formData.port"
              type="number"
              placeholder="e.g., 8000"
              min="1"
              max="65535"
              required
              class="mt-1"
            />
          </div>
        </div>

        <div>
          <Label for="nim-type">NIM Type</Label>
          <Select v-model="formData.nim_type" required>
            <SelectTrigger class="mt-1">
              <SelectValue placeholder="Select NIM type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem v-for="option in nimTypeOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Button type="submit" :disabled="isSaving || !isFormValid" class="w-full">
          <Icon name="lucide:plus" class="mr-2 h-4 w-4" />
          {{ isSaving ? 'Adding...' : (submitText || 'Add NIM Configuration') }}
        </Button>
      </form>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

// Types
interface NIMFormData {
  nim_id: string
  host: string
  port: number
  nim_type: string
}

// Props
interface Props {
  nimId?: string
  title?: string
  description?: string
  submitText?: string
  nimIdDisabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  nimIdDisabled: false,
  submitText: 'Add NIM Configuration'
})

// Emits
const emit = defineEmits<{
  submit: [data: NIMFormData]
  success: [nimId: string]
  error: [error: string]
}>()

// Reactive state
const isSaving = ref(false)

// Form data
const formData = ref<NIMFormData>({
  nim_id: '',
  host: '',
  port: 8000,
  nim_type: 'llm'
})

// NIM type options
const nimTypeOptions = [
  { value: 'llm', label: 'LLM (Large Language Model)' },
  { value: 'image_gen', label: 'Image Generation' },
  { value: '3d', label: '3D Generation' },
  { value: 'asr', label: 'Automatic Speech Recognition' },
  { value: 'tts', label: 'Text-to-Speech' },
  { value: 'studio_voice', label: 'Studio Voice' },
  { value: 'document', label: 'Document Processing' }
]

// Computed properties
const isFormValid = computed(() => {
  return formData.value.nim_id.trim() !== '' &&
         formData.value.host.trim() !== '' &&
         formData.value.port > 0 &&
         formData.value.port <= 65535 &&
         formData.value.nim_type.trim() !== ''
})

// Watch for nimId prop changes
watch(() => props.nimId, (newNimId) => {
  if (newNimId) {
    formData.value.nim_id = newNimId
  }
}, { immediate: true })

// Methods
const handleSubmit = async () => {
  if (!isFormValid.value) return

  isSaving.value = true
  try {
    emit('submit', { ...formData.value })
  } catch (error) {
    emit('error', error instanceof Error ? error.message : 'Failed to submit form')
  } finally {
    isSaving.value = false
  }
}

// Expose methods for parent components
defineExpose({
  resetForm: () => {
    formData.value = {
      nim_id: props.nimId || '',
      host: '',
      port: 8000,
      nim_type: 'llm'
    }
  },
  setSaving: (saving: boolean) => {
    isSaving.value = saving
  },
  populateForm: (config: {host: string, port: number, nim_type: string}) => {
    formData.value = {
      nim_id: props.nimId || '',
      host: config.host,
      port: config.port,
      nim_type: config.nim_type
    }
  }
})
</script>
