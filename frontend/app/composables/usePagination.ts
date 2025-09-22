export interface PaginationState {
  page: number
  limit: number
  total: number
  offset: number
}

export interface PaginationOptions {
  initialPage?: number
  initialLimit?: number
  onPageChange?: (page: number) => void
  onLimitChange?: (limit: number) => void
}

export function usePagination(options: PaginationOptions = {}) {
  const {
    initialPage = 1,
    initialLimit = 50,
    onPageChange,
    onLimitChange
  } = options

  const page = ref(initialPage)
  const limit = ref(initialLimit)
  const total = ref(0)

  const offset = computed(() => (page.value - 1) * limit.value)
  const totalPages = computed(() => Math.ceil(total.value / limit.value))
  const hasNextPage = computed(() => page.value < totalPages.value)
  const hasPreviousPage = computed(() => page.value > 1)

  function setPage(newPage: number) {
    if (newPage >= 1 && newPage <= totalPages.value) {
      page.value = newPage
      onPageChange?.(newPage)
    }
  }

  function setLimit(newLimit: number) {
    if (newLimit > 0) {
      limit.value = newLimit
      page.value = 1 // Reset to first page when limit changes
      onLimitChange?.(newLimit)
    }
  }

  function setTotal(newTotal: number) {
    total.value = newTotal
  }

  function nextPage() {
    if (hasNextPage.value) {
      setPage(page.value + 1)
    }
  }

  function previousPage() {
    if (hasPreviousPage.value) {
      setPage(page.value - 1)
    }
  }

  function firstPage() {
    setPage(1)
  }

  function lastPage() {
    setPage(totalPages.value)
  }

  return {
    // State
    page: readonly(page),
    limit: readonly(limit),
    total: readonly(total),
    offset: readonly(offset),

    // Computed
    totalPages: readonly(totalPages),
    hasNextPage: readonly(hasNextPage),
    hasPreviousPage: readonly(hasPreviousPage),

    // Actions
    setPage,
    setLimit,
    setTotal,
    nextPage,
    previousPage,
    firstPage,
    lastPage
  }
}
