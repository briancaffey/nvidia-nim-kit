<template>
  <div class="flex items-center justify-between px-2">
    <div class="flex-1 text-sm text-muted-foreground">
      Showing {{ startItem }} to {{ endItem }} of {{ total }} results
    </div>

    <div v-if="unref(totalPages) > 1" class="flex items-center space-x-2">
      <Button
        variant="outline"
        size="sm"
        :disabled="!unref(hasPreviousPage)"
        @click="firstPage"
      >
        First
      </Button>
      <Button
        variant="outline"
        size="sm"
        :disabled="!unref(hasPreviousPage)"
        @click="previousPage"
      >
        Previous
      </Button>

      <div class="flex items-center space-x-1">
        <template v-for="pageNumber in visiblePages" :key="pageNumber">
          <Button
            v-if="isNumber(pageNumber)"
            variant="outline"
            size="sm"
            :class="pageNumber === unref(page) ? 'bg-primary text-white dark:bg-white dark:text-black' : ''"
            @click="setPage(pageNumber)"
          >
            {{ pageNumber }}
          </Button>
          <span v-else class="px-2 text-muted-foreground">...</span>
        </template>
      </div>

      <Button
        variant="outline"
        size="sm"
        :disabled="!unref(hasNextPage)"
        @click="nextPage"
      >
        Next
      </Button>
      <Button
        variant="outline"
        size="sm"
        :disabled="!unref(hasNextPage)"
        @click="lastPage"
      >
        Last
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button } from '~/components/ui/button'

interface Props {
  page: number
  total: number
  limit: number
  totalPages: number
  hasNextPage: boolean
  hasPreviousPage: boolean
  setPage: (page: number) => void
  nextPage: () => void
  previousPage: () => void
  firstPage: () => void
  lastPage: () => void
}

const props = defineProps<Props>()

// Calculate visible page numbers with ellipsis
const visiblePages = computed(() => {
  const page = unref(props.page)
  const totalPages = unref(props.totalPages)
  const pages: (number | string)[] = []

  if (totalPages <= 7) {
    // Show all pages if total is small
    for (let i = 1; i <= totalPages; i++) {
      pages.push(i)
    }
  } else {
    // Show first page, last page, current page, and neighbors
    if (page <= 4) {
      // Near the beginning
      for (let i = 1; i <= 5; i++) {
        pages.push(i)
      }
      pages.push('...')
      pages.push(totalPages)
    } else if (page >= totalPages - 3) {
      // Near the end
      pages.push(1)
      pages.push('...')
      for (let i = totalPages - 4; i <= totalPages; i++) {
        pages.push(i)
      }
    } else {
      // In the middle
      pages.push(1)
      pages.push('...')
      for (let i = page - 1; i <= page + 1; i++) {
        pages.push(i)
      }
      pages.push('...')
      pages.push(totalPages)
    }
  }

  return pages
})

// Helper function to check if pageNumber is a number
const isNumber = (value: number | string): value is number => {
  return typeof value === 'number'
}

// Calculate start and end item numbers for display
const startItem = computed(() => {
  const total = unref(props.total)
  const page = unref(props.page)
  const limit = unref(props.limit)
  return total === 0 ? 0 : (page - 1) * limit + 1
})

const endItem = computed(() => {
  const page = unref(props.page)
  const limit = unref(props.limit)
  const total = unref(props.total)
  return Math.min(page * limit, total)
})
</script>
