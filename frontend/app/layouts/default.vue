<template>
  <div class="min-h-screen bg-background dark:bg-[#181818]">
    <!-- Navigation Bar -->
    <nav class="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 dark:bg-[#181818]/95">
      <div class="container mx-auto px-4">
        <div class="flex h-16 items-center justify-between">
          <!-- Logo/Brand -->
          <div class="flex items-center space-x-2">
            <NuxtLink to="/" class="flex items-center">
              <Logo width="40" height="40" />
              <span class="text-xl font-bold">NIM Kit</span>
            </NuxtLink>
          </div>

          <!-- Navigation Links -->
          <div class="hidden md:flex items-center space-x-6">
            <!-- NVIDIA API Toggle -->
            <div class="flex items-center space-x-2">
              <NuxtLink
                to="/nvidia-config"
                class="text-sm font-medium transition-colors hover:text-primary"
                :class="[
                  useNvidiaApi ? 'text-[#74b900]' : (isActive('/nvidia-config') ? 'text-primary' : 'text-muted-foreground')
                ]"
              >
                NVIDIA Config
              </NuxtLink>
              <Switch
                id="nvidia-api-toggle"
                v-model="useNvidiaApi"
                :disabled="!canEnable"
                class="data-[state=checked]:bg-primary"
              />
            </div>
            <NuxtLink
              to="/nim-config"
              class="text-sm font-medium transition-colors hover:text-primary"
              :class="isActive('/nim-config') ? 'text-primary' : 'text-muted-foreground'"
            >
              NIM Config
            </NuxtLink>
            <NuxtLink
              to="/nims"
              class="text-sm font-medium transition-colors hover:text-primary"
              :class="isActive('/nims') ? 'text-primary' : 'text-muted-foreground'"
            >
              NIMs
            </NuxtLink>
            <NuxtLink
              to="/gallery"
              class="text-sm font-medium transition-colors hover:text-primary"
              :class="isActive('/gallery') ? 'text-primary' : 'text-muted-foreground'"
            >
              Gallery
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
            <!-- NVIDIA API Toggle for Mobile -->
            <div class="flex items-center justify-between px-2 py-1">
              <NuxtLink
                to="/nvidia-config"
                class="text-sm font-medium transition-colors hover:text-primary px-2 py-1 rounded-md"
                :class="[
                  useNvidiaApi ? 'text-[#74b900]' : (isActive('/nvidia-config') ? 'text-primary bg-accent' : 'text-muted-foreground')
                ]"
                @click="mobileMenuOpen = false"
              >
                NVIDIA Config
              </NuxtLink>
              <Switch
                id="nvidia-api-toggle-mobile"
                v-model="useNvidiaApi"
                :disabled="!canEnable"
                class="data-[state=checked]:bg-primary"
              />
            </div>
            <NuxtLink
              to="/nim-config"
              class="text-sm font-medium transition-colors hover:text-primary px-2 py-1 rounded-md"
              :class="isActive('/nim-config') ? 'text-primary bg-accent' : 'text-muted-foreground'"
              @click="mobileMenuOpen = false"
            >
              NIM Config
            </NuxtLink>
            <NuxtLink
              to="/nims"
              class="text-sm font-medium transition-colors hover:text-primary px-2 py-1 rounded-md"
              :class="isActive('/nims') ? 'text-primary bg-accent' : 'text-muted-foreground'"
              @click="mobileMenuOpen = false"
            >
              NIMs
            </NuxtLink>
            <NuxtLink
              to="/gallery"
              class="text-sm font-medium transition-colors hover:text-primary px-2 py-1 rounded-md"
              :class="isActive('/gallery') ? 'text-primary bg-accent' : 'text-muted-foreground'"
              @click="mobileMenuOpen = false"
            >
              Gallery
            </NuxtLink>
            <NuxtLink
              to="/tres"
              class="text-sm font-medium transition-colors hover:text-primary px-2 py-1 rounded-md"
              :class="isActive('/tres') ? 'text-primary bg-accent' : 'text-muted-foreground'"
              @click="mobileMenuOpen = false"
            >
              TresJS
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
    <footer class="border-t bg-background dark:bg-[#181818] mt-auto">
      <div class="container mx-auto px-4 py-12">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
          <!-- Brand Section -->
          <div class="md:col-span-2">
            <div class="flex items-center mb-4">
              <Logo width="40" height="40" />
              <span class="text-xl font-bold">NIM Kit</span>
            </div>
            <p class="text-muted-foreground mb-4 max-w-md">
              A comprehensive toolkit for NVIDIA Inference Microservices (NIMs).
              Generate images with Flux models, chat with LLMs, and explore the power of AI inference.
            </p>
            <div class="flex space-x-4">
              <a
                href="https://github.com/nvidia/nim-kit"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center space-x-2 text-muted-foreground hover:text-primary transition-colors"
              >
                <Icon name="lucide:github" class="h-5 w-5" />
                <span>GitHub</span>
              </a>
              <a
                href="https://docs.nvidia.com/nim/"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center space-x-2 text-muted-foreground hover:text-primary transition-colors"
              >
                <Icon name="lucide:book-open" class="h-5 w-5" />
                <span>NIM Docs</span>
              </a>
            </div>
          </div>

          <!-- Quick Links -->
          <div>
            <h3 class="font-semibold mb-4">Quick Links</h3>
            <ul class="space-y-2">
              <li>
                <NuxtLink to="/" class="text-muted-foreground hover:text-primary transition-colors">
                  Home
                </NuxtLink>
              </li>
              <li>
                <NuxtLink to="/nims" class="text-muted-foreground hover:text-primary transition-colors">
                  NIMs Catalog
                </NuxtLink>
              </li>
              <li>
                <NuxtLink to="/gallery" class="text-muted-foreground hover:text-primary transition-colors">
                  Gallery
                </NuxtLink>
              </li>
              <li>
                <NuxtLink to="/about" class="text-muted-foreground hover:text-primary transition-colors">
                  About
                </NuxtLink>
              </li>
            </ul>
          </div>

          <!-- Resources -->
          <div>
            <h3 class="font-semibold mb-4">Resources</h3>
            <ul class="space-y-2">
              <li>
                <a
                  href="https://github.com/nvidia/nim-kit/blob/main/README.md"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-muted-foreground hover:text-primary transition-colors"
                >
                  Documentation
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/nvidia/nim-kit/issues"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-muted-foreground hover:text-primary transition-colors"
                >
                  Report Issues
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/nvidia/nim-kit/discussions"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-muted-foreground hover:text-primary transition-colors"
                >
                  Community
                </a>
              </li>
              <li>
                <a
                  href="https://www.nvidia.com/en-us/ai-data-science/"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-muted-foreground hover:text-primary transition-colors"
                >
                  NVIDIA AI
                </a>
              </li>
            </ul>
          </div>
        </div>

        <!-- Bottom Section -->
        <div class="border-t mt-8 pt-8">
          <div class="flex flex-col md:flex-row items-center justify-between gap-4">
            <p class="text-sm text-muted-foreground">
              © 2024 Community Project. Not officially associated with NVIDIA.
            </p>
            <div class="flex items-center space-x-4 text-sm text-muted-foreground">
              <span>Powered by NVIDIA NIMs</span>
              <div class="flex items-center space-x-1">
                <Icon name="lucide:zap" class="h-4 w-4 text-primary" />
                <span>Fast AI Inference</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import ThemeToggle from '~/components/ThemeToggle.vue'

const route = useRoute()
const mobileMenuOpen = ref(false)


// @ts-ignore - useColorMode is auto-imported by @nuxtjs/color-mode
const colorMode = useColorMode()

// NVIDIA API toggle
const { useNvidiaApi, canEnable, setNvidiaApi, loadFromBackend } = useNvidiaApiToggle()

// Load toggle state on mount
onMounted(() => {
  loadFromBackend()
})

const isActive = (path: string) => {
  if (!route) return false
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
