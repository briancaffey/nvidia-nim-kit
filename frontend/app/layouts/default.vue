<template>
  <div class="min-h-screen bg-background">
    <!-- Navigation Bar -->
    <nav class="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div class="container mx-auto px-4">
        <div class="flex h-16 items-center justify-between">
          <!-- Logo/Brand -->
          <div class="flex items-center space-x-2">
            <NuxtLink to="/" class="flex items-center space-x-2">
              <div class="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
                <span class="text-primary-foreground font-bold text-sm">N</span>
              </div>
              <span class="text-xl font-bold">NIM Kit</span>
            </NuxtLink>
          </div>

          <!-- Navigation Links -->
          <div class="hidden md:flex items-center space-x-6">
            <NuxtLink
              to="/"
              class="text-sm font-medium transition-colors hover:text-primary"
              :class="isActive('/') ? 'text-primary' : 'text-muted-foreground'"
            >
              Home
            </NuxtLink>
            <NuxtLink
              to="/about"
              class="text-sm font-medium transition-colors hover:text-primary"
              :class="isActive('/about') ? 'text-primary' : 'text-muted-foreground'"
            >
              About
            </NuxtLink>
            <NuxtLink
              to="/debug"
              class="text-sm font-medium transition-colors hover:text-primary"
              :class="isActive('/debug') ? 'text-primary' : 'text-muted-foreground'"
            >
              Debug
            </NuxtLink>
            <NuxtLink
              to="/nim-config"
              class="text-sm font-medium transition-colors hover:text-primary"
              :class="isActive('/nim-config') ? 'text-primary' : 'text-muted-foreground'"
            >
              NIM Config
            </NuxtLink>
            <NuxtLink
              to="/llm"
              class="text-sm font-medium transition-colors hover:text-primary"
              :class="isActive('/llm') ? 'text-primary' : 'text-muted-foreground'"
            >
              LLM
            </NuxtLink>
            <button
              @click="toggleTheme"
              class="inline-flex items-center justify-center w-9 h-9 rounded-md border border-input bg-background hover:bg-accent hover:text-accent-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              style="cursor: pointer;"
            >
              <Icon
                :name="colorMode.value === 'dark' ? 'lucide:sun' : 'lucide:moon'"
                class="h-4 w-4 transition-transform duration-300 hover:scale-110"
                :class="colorMode.value === 'dark' ? 'rotate-180' : 'rotate-0'"
              />
            </button>
          </div>

          <!-- Mobile Menu Button -->
          <div class="md:hidden">
            <Button
              variant="ghost"
              size="sm"
              @click="mobileMenuOpen = !mobileMenuOpen"
            >
              <Icon name="lucide:menu" class="h-5 w-5" />
            </Button>
          </div>
        </div>

        <!-- Mobile Menu -->
        <div v-if="mobileMenuOpen" class="md:hidden border-t py-4">
          <div class="flex flex-col space-y-2">
            <NuxtLink
              to="/"
              class="text-sm font-medium transition-colors hover:text-primary px-2 py-1 rounded-md"
              :class="isActive('/') ? 'text-primary bg-accent' : 'text-muted-foreground'"
              @click="mobileMenuOpen = false"
            >
              Home
            </NuxtLink>
            <NuxtLink
              to="/about"
              class="text-sm font-medium transition-colors hover:text-primary px-2 py-1 rounded-md"
              :class="isActive('/about') ? 'text-primary bg-accent' : 'text-muted-foreground'"
              @click="mobileMenuOpen = false"
            >
              About
            </NuxtLink>
            <NuxtLink
              to="/debug"
              class="text-sm font-medium transition-colors hover:text-primary px-2 py-1 rounded-md"
              :class="isActive('/debug') ? 'text-primary bg-accent' : 'text-muted-foreground'"
              @click="mobileMenuOpen = false"
            >
              Debug
            </NuxtLink>
            <NuxtLink
              to="/nim-config"
              class="text-sm font-medium transition-colors hover:text-primary px-2 py-1 rounded-md"
              :class="isActive('/nim-config') ? 'text-primary bg-accent' : 'text-muted-foreground'"
              @click="mobileMenuOpen = false"
            >
              NIM Config
            </NuxtLink>
            <NuxtLink
              to="/llm"
              class="text-sm font-medium transition-colors hover:text-primary px-2 py-1 rounded-md"
              :class="isActive('/llm') ? 'text-primary bg-accent' : 'text-muted-foreground'"
              @click="mobileMenuOpen = false"
            >
              LLM
            </NuxtLink>
            <div class="px-2 py-1">
              <ThemeToggle />
            </div>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="flex-1">
      <slot />
    </main>

    <!-- Footer -->
    <footer class="border-t bg-background">
      <div class="container mx-auto px-4 py-8">
        <div class="flex flex-col items-center justify-between gap-4 md:h-24 md:flex-row">
          <div class="flex flex-col items-center gap-4 px-8 md:flex-row md:gap-2 md:px-0">
            <p class="text-center text-sm leading-loose text-muted-foreground md:text-left">
              Built with Nuxt 4 and shadcn/ui. © 2024 NIM Kit.
            </p>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const mobileMenuOpen = ref(false)

// @ts-ignore - useColorMode is auto-imported by @nuxtjs/color-mode
const colorMode = useColorMode()

const isActive = (path: string) => {
  return route.path === path
}

const toggleTheme = () => {
  colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark'
}

// Close mobile menu when route changes
watch(() => route.path, () => {
  mobileMenuOpen.value = false
})
</script>
