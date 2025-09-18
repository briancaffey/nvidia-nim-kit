# Frontend Development Rules

## API Integration Pattern

When making API calls from Vue components, follow this pattern:

### 1. Get Runtime Config
```typescript
const config = useRuntimeConfig()
```

### 2. API Call Structure
```typescript
async function apiFunction() {
  if (isLoading.value) return

  isLoading.value = true

  try {
    const response = await $fetch(`${config.public.apiBase}/api/endpoint`, {
      method: 'POST', // or GET, PUT, DELETE
      body: { /* request data */ }
    })

    console.log('API response:', response)

    // Handle success
    // Update reactive state

  } catch (err) {
    console.error('API call failed:', err)
    // Handle error
    error.value = 'Error message'
  } finally {
    isLoading.value = false
  }
}
```

### 3. Required Reactive State
- `isLoading` - Boolean to prevent multiple calls
- `error` - String for error messages
- Success state variables as needed

### 4. Error Handling
- Always wrap API calls in try/catch
- Log errors to console
- Set user-friendly error messages
- Reset loading state in finally block

### 5. Loading States
- Disable buttons/forms when loading
- Show loading indicators
- Prevent multiple simultaneous calls
