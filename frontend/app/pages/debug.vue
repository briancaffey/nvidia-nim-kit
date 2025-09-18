<template>
  <div class="container mx-auto px-4 py-12">
    <div class="max-w-2xl mx-auto">
      <!-- Header -->
      <div class="text-center mb-12">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-6">
          <Icon name="lucide:bug" class="h-8 w-8 text-primary" />
        </div>
        <h1 class="text-4xl font-bold tracking-tight mb-4">Debug</h1>
        <p class="text-xl text-muted-foreground">
          Test backend API integration
        </p>
      </div>

      <!-- Main Card -->
      <Card class="p-8">
        <div class="text-center space-y-6">
          <div>
            <h2 class="text-2xl font-semibold mb-2">Trigger Debug Task</h2>
            <p class="text-muted-foreground">
              This will trigger a Celery task that sleeps for 1 second
            </p>
          </div>

          <Button
            @click="triggerDebugTask"
            :disabled="isLoading"
            class="w-full h-12 text-lg font-semibold"
            size="lg"
          >
            <Icon
              :name="isLoading ? 'lucide:loader-2' : 'lucide:play'"
              :class="isLoading ? 'animate-spin' : ''"
              class="mr-3 h-5 w-5"
            />
            {{ isLoading ? 'Processing...' : 'Run Debug Task' }}
          </Button>

          <!-- Success Message -->
          <Alert v-if="success" class="border-green-200 bg-green-50">
            <Icon name="lucide:check-circle" class="h-4 w-4 text-green-600" />
            <AlertTitle class="text-green-800">Success!</AlertTitle>
            <AlertDescription class="text-green-700">
              Debug task triggered successfully
            </AlertDescription>
          </Alert>

          <!-- Error Message -->
          <Alert v-if="error" variant="destructive">
            <Icon name="lucide:alert-circle" class="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>
              {{ error }}
            </AlertDescription>
          </Alert>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
// Set page metadata
useHead({
  title: 'Debug - NIM Kit',
  meta: [
    { name: 'description', content: 'Debug page for testing backend API integration and Celery tasks.' }
  ]
})

// Reactive state
const isLoading = ref(false)
const error = ref<string | null>(null)
const success = ref<string | null>(null)

// Get runtime config for API base URL
const config = useRuntimeConfig()

// Trigger debug task function
async function triggerDebugTask() {
  if (isLoading.value) return

  isLoading.value = true
  error.value = null
  success.value = null

  try {
    const response = await $fetch<{ task_id: string; status: string }>(`${config.public.apiBase}/api/tasks/debug`, {
      method: 'POST'
    })

    console.log('Debug task triggered:', response)

    success.value = 'Debug task triggered successfully!'

  } catch (err) {
    console.error('Failed to trigger debug task:', err)
    error.value = 'Failed to trigger debug task. Make sure the backend is running.'
  } finally {
    isLoading.value = false
  }
}
</script>
