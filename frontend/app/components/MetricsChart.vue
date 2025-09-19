<template>
  <div class="w-full h-full">
    <!-- Chart Container -->
    <div v-if="chartData.length > 0" class="h-full">
      <!-- Histogram Chart (Bar Chart) -->
      <BarChart
        v-if="isHistogramMetric"
        :data="histogramData"
        :categories="['value']"
        :index="'bucket'"
        :colors="chartColors"
        :x-formatter="formatHistogramXAxis"
        :y-formatter="formatYAxis"
        :show-tooltip="true"
        :show-legend="false"
        :show-grid-line="true"
        :tooltip-formatter="formatHistogramTooltip"
        class="h-full"
      />

      <!-- Line Chart -->
      <LineChart
        v-else-if="chartType === 'line'"
        :data="chartData"
        :categories="['value']"
        :index="'timestamp'"
        :colors="chartColors"
        :x-formatter="formatXAxis"
        :y-formatter="formatYAxis"
        :show-tooltip="true"
        :show-legend="false"
        :show-grid-line="true"
        class="h-full"
      />

      <!-- Area Chart -->
      <AreaChart
        v-else-if="chartType === 'area'"
        :data="chartData"
        :categories="['value']"
        :index="'timestamp'"
        :colors="chartColors"
        :x-formatter="formatXAxis"
        :y-formatter="formatYAxis"
        :show-tooltip="true"
        :show-legend="false"
        :show-grid-line="true"
        :show-gradient="true"
        class="h-full"
      />
    </div>

    <!-- Empty State -->
    <div v-else class="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
      <div class="text-center">
        <Icon name="lucide:bar-chart-3" class="h-8 w-8 mx-auto mb-2" />
        <p class="text-sm">No data available</p>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center h-full">
      <div class="flex items-center space-x-2">
        <Icon name="lucide:loader-2" class="h-4 w-4 animate-spin" />
        <span class="text-sm">Loading chart...</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { LineChart } from '@/components/ui/chart-line'
import { AreaChart } from '@/components/ui/chart-area'
import { BarChart } from '@/components/ui/chart-bar'

// Props
interface Props {
  data: Array<{
    timestamp: string
    value: number
    index: number
  }>
  chartType: 'line' | 'area' | 'histogram'
  metricName: string
  aggregation: string
  bucketSize: string
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// Computed properties
const isHistogramMetric = computed(() => {
  return props.metricName.includes('_bucket') ||
         props.metricName.includes('histogram') ||
         props.chartType === 'histogram'
})

const chartData = computed(() => {
  if (!props.data || props.data.length === 0) return []

  // Sort data by timestamp
  return [...props.data].sort((a, b) =>
    new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  )
})

const histogramData = computed(() => {
  if (!isHistogramMetric.value || !props.data || props.data.length === 0) return []

  // For histograms, we want to show the distribution at the latest timestamp
  // Group data by bucket (index) and take the latest value for each bucket
  const latestData = props.data.reduce((acc, item) => {
    const bucketKey = `bucket_${item.index}`
    if (!acc[bucketKey] || new Date(item.timestamp) > new Date(acc[bucketKey].timestamp)) {
      acc[bucketKey] = item
    }
    return acc
  }, {} as Record<string, typeof props.data[0]>)

  // Convert to histogram format with bucket labels
  const bucketLabels = [
    '≤1.0', '≤2.0', '≤5.0', '≤10.0', '≤20.0', '≤50.0',
    '≤100.0', '≤200.0', '≤500.0', '≤1000.0', '≤2000.0',
    '≤5000.0', '≤10000.0', '≤20000.0', '+Inf'
  ]

  return Object.values(latestData)
    .sort((a, b) => a.index - b.index)
    .map((item, idx) => ({
      bucket: bucketLabels[idx] || `≤${(idx + 1) * 10}`,
      value: item.value,
      index: item.index,
      timestamp: item.timestamp,
      // Add descriptive label for tooltips
      label: `${bucketLabels[idx] || `≤${(idx + 1) * 10}`} (${item.value.toLocaleString()} values)`
    }))
})

const chartColors = computed(() => {
  // Return appropriate colors based on metric type
  const metricName = props.metricName.toLowerCase()

  if (metricName.includes('error') || metricName.includes('failure')) {
    return ['#ef4444'] // Red for errors
  } else if (metricName.includes('latency') || metricName.includes('time')) {
    return ['#f59e0b'] // Orange for latency
  } else if (metricName.includes('token')) {
    return ['#3b82f6'] // Blue for tokens
  } else if (metricName.includes('request') || metricName.includes('running')) {
    return ['#10b981'] // Green for requests
  } else if (metricName.includes('usage') || metricName.includes('cache')) {
    return ['#8b5cf6'] // Purple for usage
  } else {
    return ['#6b7280'] // Gray for other metrics
  }
})

// Formatters
const formatXAxis = (value: number) => {
  if (props.data && props.data[value]) {
    const timestamp = props.data[value].timestamp
    const date = new Date(timestamp)

    // Format based on time range
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffHours = diffMs / (1000 * 60 * 60)

    if (diffHours < 1) {
      // Show minutes:seconds for recent data
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    } else if (diffHours < 24) {
      // Show hours:minutes for today
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
      })
    } else {
      // Show date for older data
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
  }
  return value.toString()
}

const formatHistogramXAxis = (tick: number | Date, i: number, ticks: (number | Date)[]) => {
  // For histogram charts, the index corresponds to the data array position
  console.log('Formatting histogram X-axis for tick:', tick, 'index:', i, 'Data:', histogramData.value[i])
  if (histogramData.value && histogramData.value[i]) {
    return histogramData.value[i].bucket
  }
  return `Bucket ${i}`
}

const formatHistogramTooltip = (data: any) => {
  if (!data || !data.data) return ''

  const bucket = data.data.bucket || 'Unknown'
  const value = data.data.value || 0
  const timestamp = data.data.timestamp

  // Format timestamp for tooltip
  const date = new Date(timestamp)
  const timeStr = date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })

  return `${bucket}\nCount: ${value.toLocaleString()}\nTime: ${timeStr}`
}

const formatYAxis = (value: number) => {
  // Format based on metric type and value
  const metricName = props.metricName.toLowerCase()

  if (metricName.includes('time') || metricName.includes('latency')) {
    // Time-based metrics - show in appropriate units
    if (value < 1) {
      return `${(value * 1000).toFixed(0)}ms`
    } else if (value < 60) {
      return `${value.toFixed(2)}s`
    } else {
      return `${(value / 60).toFixed(1)}m`
    }
  } else if (metricName.includes('token')) {
    // Token counts - show with K/M suffixes
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`
    } else if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`
    } else {
      return value.toFixed(0)
    }
  } else if (metricName.includes('usage') || metricName.includes('cache')) {
    // Percentage or ratio metrics
    if (value <= 1) {
      return `${(value * 100).toFixed(1)}%`
    } else {
      return value.toFixed(2)
    }
  } else {
    // Default formatting
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`
    } else if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`
    } else if (value % 1 !== 0) {
      return value.toFixed(2)
    } else {
      return value.toFixed(0)
    }
  }
}
</script>
