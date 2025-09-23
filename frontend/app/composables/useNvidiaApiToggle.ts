import { ref, readonly, watch } from 'vue'

// Global state for NVIDIA API toggle
const useNvidiaApi = ref(false)
const canEnable = ref(false)
let isLoaded = false

export const useNvidiaApiToggle = () => {
  // Watch for changes to useNvidiaApi and save to backend
  watch(useNvidiaApi, (newValue, oldValue) => {
    // Only save if this is a user-initiated change (not from loading from backend)
    if (oldValue !== undefined && newValue !== oldValue && isLoaded) {
      console.log('🎛️ useNvidiaApi changed from', oldValue, 'to', newValue)
      saveToBackend(newValue)
    }
  })

  // Load from backend
  const loadFromBackend = async () => {
    console.log('🔄 Loading NVIDIA API toggle from backend...')
    try {
      const config = useRuntimeConfig()
      const response = await fetch(`${config.public.apiBase}/api/nvidia/toggle`)
      console.log('📡 Load response status:', response.status)

      if (response.ok) {
        const data = await response.json()
        console.log('✅ Load response data:', data)
        useNvidiaApi.value = data.enabled
        canEnable.value = data.can_enable
        isLoaded = true
      }
    } catch (error) {
      console.error('❌ Failed to load NVIDIA API toggle state:', error)
    }
  }

  // Save to backend
  const saveToBackend = async (enabled: boolean) => {
    console.log('🔄 Saving NVIDIA API toggle to backend:', enabled)
    try {
      const config = useRuntimeConfig()
      const response = await fetch(`${config.public.apiBase}/api/nvidia/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled })
      })

      console.log('📡 Backend response status:', response.status)

      if (response.ok) {
        const data = await response.json()
        console.log('✅ Backend response data:', data)
        useNvidiaApi.value = data.enabled
        canEnable.value = data.can_enable
      } else {
        const errorData = await response.json()
        console.error('❌ Failed to save NVIDIA API toggle:', errorData.detail)
      }
    } catch (error) {
      console.error('❌ Failed to save NVIDIA API toggle state:', error)
    }
  }

  return {
    useNvidiaApi, // Make it writable for v-model
    canEnable: readonly(canEnable),
    loadFromBackend,
    toggleNvidiaApi: () => {
      useNvidiaApi.value = !useNvidiaApi.value
    },
    setNvidiaApi: (enabled: boolean) => {
      console.log('🎛️ setNvidiaApi called with:', enabled)
      useNvidiaApi.value = enabled
    }
  }
}
