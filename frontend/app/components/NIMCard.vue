<template>
  <NuxtLink :to="`/nims/${publisher}/${modelName}`" class="block">
    <Card class="group hover:shadow-lg transition-all duration-200 overflow-hidden cursor-pointer !p-0 !gap-0">
      <!-- Image Section -->
      <div class="relative h-48 bg-gradient-to-br from-primary/20 to-primary/5 overflow-hidden">
        <NuxtImg
          :src="imageUrl"
          :alt="nim.id"
          class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          loading="lazy"
          :placeholder="[16, 16, 75, 5]"
        />
        <!-- Overlay gradient for better text readability -->
        <div class="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent" />
      </div>

    <!-- Content Section -->
    <CardContent class="p-6">
      <!-- Publisher/Namespace -->
      <div class="text-sm text-muted-foreground mb-1">
        {{ publisher }}
      </div>

      <!-- Title -->
      <CardTitle class="text-lg font-semibold mb-3 line-clamp-2 group-hover:text-primary transition-colors">
        {{ modelName }}
      </CardTitle>

      <!-- Description -->
      <p class="text-sm text-muted-foreground mb-4 line-clamp-2">
        {{ nim.description }}
      </p>

      <!-- Tags -->
      <div class="flex flex-wrap gap-2">
        <Badge
          v-for="tag in visibleTags"
          :key="tag"
          variant="secondary"
          class="text-xs"
        >
          {{ tag }}
        </Badge>
        <Tooltip v-if="remainingTagsCount > 0">
          <TooltipTrigger as-child>
            <Badge
              variant="outline"
              class="text-xs cursor-help"
            >
              +{{ remainingTagsCount }}
            </Badge>
          </TooltipTrigger>
          <TooltipContent>
            <div class="flex flex-wrap gap-1">
              <span
                v-for="tag in remainingTags"
                :key="tag"
                class="text-xs bg-secondary text-secondary-foreground px-2 py-1 rounded"
              >
                {{ tag }}
              </span>
            </div>
          </TooltipContent>
        </Tooltip>
      </div>
    </CardContent>
    </Card>
  </NuxtLink>
</template>

<script setup lang="ts">
interface NIM {
  id: string
  url: string
  invoke_url?: string
  model?: string
  type: string
  tags: string[]
  description: string
  release_date?: string
  img: string
}

interface Props {
  nim: NIM
}

const props = defineProps<Props>()
const config = useRuntimeConfig()

// Split the ID into publisher and model name
const [publisher, modelName] = props.nim.id.split('/')

// Construct image URL
const imageUrl = computed(() => {
  return `${config.public.apiBase}/static/nims/${props.nim.img}`
})

// Show only first 3 tags, with a count for remaining
const visibleTags = computed(() => {
  return props.nim.tags.slice(0, 3)
})

const remainingTags = computed(() => {
  return props.nim.tags.slice(3)
})

const remainingTagsCount = computed(() => {
  return Math.max(0, props.nim.tags.length - 3)
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
