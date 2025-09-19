<template>
  <div class="container mx-auto px-4 py-8 max-w-7xl">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
        LLM Metrics Dashboard
      </h1>
      <p class="text-gray-600 dark:text-gray-400">
        Monitor and analyze LLM performance metrics in real-time
      </p>
      <NuxtLink to="/llm" class="text-blue-500 hover:underline">← Back to LLM</NuxtLink>
    </div>

    <!-- Error Alert -->
    <Alert v-if="error" variant="destructive" class="mb-6">
      <AlertTitle>Error</AlertTitle>
      <AlertDescription>{{ error }}</AlertDescription>
    </Alert>

    <!-- Controls Panel -->
    <Card class="mb-8">
      <CardHeader>
        <CardTitle class="flex items-center gap-2">
          <Icon name="lucide:sliders-horizontal" class="h-5 w-5" />
          Query Controls
        </CardTitle>
        <CardDescription>
          Configure time range, metrics, and visualization options
        </CardDescription>
      </CardHeader>
      <CardContent class="space-y-6">
        <!-- Time Range Controls -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="space-y-2">
            <Label for="time-range">Time Range</Label>
            <Select v-model="timeRange" @update:model-value="updateTimeRange">
              <SelectTrigger>
                <SelectValue placeholder="Select time range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="5m">Last 5 minutes</SelectItem>
                <SelectItem value="15m">Last 15 minutes</SelectItem>
                <SelectItem value="1h">Last 1 hour</SelectItem>
                <SelectItem value="6h">Last 6 hours</SelectItem>
                <SelectItem value="24h">Last 24 hours</SelectItem>
                <SelectItem value="7d">Last 7 days</SelectItem>
                <SelectItem value="custom">Custom range</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div v-if="timeRange === 'custom'" class="space-y-2">
            <Label for="start-time">Start Time</Label>
            <Input
              id="start-time"
              v-model="customStartTime"
              type="datetime-local"
              @change="updateCustomTimeRange"
            />
          </div>

          <div v-if="timeRange === 'custom'" class="space-y-2">
            <Label for="end-time">End Time</Label>
            <Input
              id="end-time"
              v-model="customEndTime"
              type="datetime-local"
              @change="updateCustomTimeRange"
            />
          </div>

          <div class="space-y-2">
            <Label for="refresh-interval">Auto Refresh</Label>
            <Select v-model="refreshInterval" @update:model-value="updateRefreshInterval">
              <SelectTrigger>
                <SelectValue placeholder="Refresh interval" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="0">Off</SelectItem>
                <SelectItem value="5">5 seconds</SelectItem>
                <SelectItem value="10">10 seconds</SelectItem>
                <SelectItem value="30">30 seconds</SelectItem>
                <SelectItem value="60">1 minute</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <!-- Metric Selection -->
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <Label>Available Metrics ({{ availableMetrics.length }})</Label>
            <Button variant="outline" size="sm" @click="loadAvailableMetrics">
              <Icon name="lucide:refresh-cw" class="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>

          <div v-if="availableMetrics.length === 0" class="text-sm text-gray-500">
            No metrics loaded yet. Click Refresh to load available metrics.
          </div>
          <div v-else class="text-sm text-green-600 mb-2">
            Found {{ groupedMetrics.length }} metric groups available for selection.
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <div v-for="group in groupedMetrics" :key="group.name" class="border rounded-lg p-3">
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center space-x-2 min-w-0 flex-1">
                  <input
                    type="checkbox"
                    :id="`group-${group.name}`"
                    :checked="isGroupSelected(group)"
                    @change="toggleGroup(group)"
                    class="mr-2 flex-shrink-0"
                  />
                  <Label :for="`group-${group.name}`" class="text-sm font-medium cursor-pointer truncate">
                    {{ group.name }}
                  </Label>
                </div>
                <div class="flex items-center space-x-1 flex-shrink-0">
                  <Badge :variant="group.type === 'histogram' ? 'default' : group.type === 'counter' ? 'secondary' : 'outline'" class="text-xs">
                    {{ group.type }}
                  </Badge>
                  <span class="text-xs text-gray-500">
                    {{ group.buckets.length }}
                  </span>
                </div>
              </div>

              <!-- Histogram buckets (compact) -->
              <div v-if="group.type === 'histogram' && isGroupSelected(group)" class="ml-6">
                <div class="text-xs text-gray-600 mb-1">Buckets:</div>
                <div class="flex flex-wrap gap-1">
                  <span v-for="(bucket, index) in group.buckets.slice(0, 6)" :key="bucket.key" class="text-xs text-gray-500 bg-gray-100 px-1 rounded">
                    {{ getBucketLabel(bucket.key, index) }}
                  </span>
                  <span v-if="group.buckets.length > 6" class="text-xs text-gray-400">
                    +{{ group.buckets.length - 6 }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Aggregation Controls -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="space-y-2">
            <Label for="aggregation">Aggregation</Label>
            <Select v-model="aggregation" @update:model-value="loadMetrics">
              <SelectTrigger>
                <SelectValue placeholder="Select aggregation" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None (Raw data)</SelectItem>
                <SelectItem value="avg">Average</SelectItem>
                <SelectItem value="sum">Sum</SelectItem>
                <SelectItem value="min">Minimum</SelectItem>
                <SelectItem value="max">Maximum</SelectItem>
                <SelectItem value="count">Count</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div v-if="aggregation !== 'none'" class="space-y-2">
            <Label for="bucket-size">Bucket Size</Label>
            <Select v-model="bucketSize" @update:model-value="loadMetrics">
              <SelectTrigger>
                <SelectValue placeholder="Select bucket size" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="5000">5 seconds</SelectItem>
                <SelectItem value="10000">10 seconds</SelectItem>
                <SelectItem value="30000">30 seconds</SelectItem>
                <SelectItem value="60000">1 minute</SelectItem>
                <SelectItem value="300000">5 minutes</SelectItem>
                <SelectItem value="600000">10 minutes</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="space-y-2">
            <Label for="chart-type">Chart Type</Label>
            <Select v-model="chartType" @update:model-value="loadMetrics">
              <SelectTrigger>
                <SelectValue placeholder="Select chart type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="line">Line Chart</SelectItem>
                <SelectItem value="area">Area Chart</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex justify-between items-center">
          <div class="flex items-center gap-4">
            <Button @click="loadMetrics" :disabled="loading || selectedMetrics.length === 0">
              <Icon name="lucide:play" class="h-4 w-4 mr-2" />
              Load Metrics
            </Button>
            <div class="text-sm text-gray-600">
              Selected: {{ selectedMetrics.length }} | Loading: {{ loading }}
            </div>
          </div>

          <div class="flex items-center space-x-2">
            <Button variant="outline" @click="exportData" :disabled="!metricsData.length">
              <Icon name="lucide:download" class="h-4 w-4 mr-2" />
              Export
            </Button>
            <Button variant="outline" @click="clearData">
              <Icon name="lucide:trash-2" class="h-4 w-4 mr-2" />
              Clear
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="flex items-center space-x-2">
        <Icon name="lucide:loader-2" class="h-4 w-4 animate-spin" />
        <span>Loading metrics...</span>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!metricsData.length && !loading" class="text-center py-12">
      <Icon name="lucide:bar-chart-3" class="h-12 w-12 mx-auto text-gray-400 mb-4" />
      <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
        No metrics data available
      </h3>
      <p class="text-gray-600 dark:text-gray-400 mb-4">
        Select metrics and click "Load Metrics" to start viewing data
      </p>
      <div v-if="selectedMetrics.length > 0" class="text-sm text-blue-600 mb-4">
        {{ selectedMetrics.length }} metrics selected
      </div>
      <Button @click="loadMetrics" :disabled="selectedMetrics.length === 0">
        <Icon name="lucide:play" class="h-4 w-4 mr-2" />
        Load Metrics
      </Button>
    </div>

    <!-- Metrics Visualization -->
    <div v-else class="space-y-8">
      <!-- Summary Stats -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card v-for="stat in summaryStats" :key="stat.label">
          <CardContent class="p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-gray-600 dark:text-gray-400">{{ stat.label }}</p>
                <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ stat.value }}</p>
              </div>
              <Icon :name="stat.icon" class="h-8 w-8 text-gray-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- Charts -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card v-for="metric in selectedMetrics" :key="metric" class="col-span-1">
          <CardHeader>
            <CardTitle class="flex items-center justify-between">
              <span>{{ getMetricDisplayName(metric) }}</span>
              <div class="flex items-center space-x-2">
                <Badge variant="outline">{{ getMetricType(metric) }}</Badge>
                <Badge variant="secondary">{{ getChartTypeForMetric(metric) }}</Badge>
              </div>
            </CardTitle>
            <CardDescription class="space-y-2">
              <div>{{ getMetricDescription(metric) }}</div>
              <div class="text-sm text-muted-foreground">
                {{ getChartMetadata(metric) }}
              </div>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div class="h-[400px]">
              <MetricsChart
                :data="getChartData(metric)"
                :chart-type="getChartTypeForMetric(metric)"
                :metric-name="metric"
                :aggregation="aggregation"
                :bucket-size="bucketSize"
              />
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- Raw Data Table -->
      <Card>
        <CardHeader>
          <CardTitle>Raw Data</CardTitle>
          <CardDescription>
            Latest data points for selected metrics
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div class="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Metric</TableHead>
                  <TableHead>Labels</TableHead>
                  <TableHead>Latest Value</TableHead>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>Data Points</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-for="series in metricsData" :key="series.key">
                  <TableCell class="font-medium">
                    {{ series.labels.metric || 'Unknown' }}
                  </TableCell>
                  <TableCell>
                    <div class="flex flex-wrap gap-1">
                      <Badge
                        v-for="(value, key) in series.labels"
                        :key="key"
                        variant="secondary"
                        class="text-xs"
                      >
                        {{ key }}: {{ value }}
                      </Badge>
                    </div>
                  </TableCell>
                  <TableCell class="font-mono">
                    {{ series.samples.length > 0 ? series.samples[series.samples.length - 1][1] : 'N/A' }}
                  </TableCell>
                  <TableCell class="text-sm text-gray-600 dark:text-gray-400">
                    {{ series.samples.length > 0 ? formatTimestamp(series.samples[series.samples.length - 1][0]) : 'N/A' }}
                  </TableCell>
                  <TableCell>
                    {{ series.samples.length }}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import MetricsChart from '@/components/MetricsChart.vue'

// Runtime config
const runtimeConfig = useRuntimeConfig()
const apiBase = runtimeConfig.public.apiBase || 'http://localhost:8000'

// Debug logging
console.log('Runtime config:', runtimeConfig)
console.log('API Base:', apiBase)

// Types
interface MetricSeries {
  key: string
  labels: Record<string, string>
  samples: [number, number][]
}

interface MetricKey {
  key: string
  labels: Record<string, string>
}

interface HistogramGroup {
  name: string
  type: 'histogram' | 'counter' | 'gauge'
  buckets: MetricKey[]
  sum?: MetricKey
  count?: MetricKey
}

// Reactive state
const loading = ref(false)
const error = ref('')
const metricsData = ref<MetricSeries[]>([])
const availableMetrics = ref<MetricKey[]>([])
const selectedMetrics = ref<string[]>([])
const refreshInterval = ref('30')
const refreshTimer = ref<number | null>(null)

// Grouped metrics for better organization
const groupedMetrics = computed(() => {
  const groups: HistogramGroup[] = []
  const processed = new Set<string>()

  for (const metric of availableMetrics.value) {
    const metricName = metric.labels?.metric
    if (!metricName || processed.has(metricName)) continue

    if (metricName.includes('_bucket')) {
      // This is a histogram bucket - group all related metrics
      const baseName = metricName.replace('_bucket', '')
      const buckets = availableMetrics.value.filter(m =>
        m.labels?.metric === metricName && m.labels?.metric?.includes('_bucket')
      )
      const sum = availableMetrics.value.find(m => m.labels?.metric === `${baseName}_sum`)
      const count = availableMetrics.value.find(m => m.labels?.metric === `${baseName}_count`)

      if (buckets.length > 0) {
        groups.push({
          name: baseName,
          type: 'histogram',
          buckets: buckets.sort((a, b) => {
            const aLe = a.labels?.metric?.match(/le="([^"]+)"/)?.[1] || '0'
            const bLe = b.labels?.metric?.match(/le="([^"]+)"/)?.[1] || '0'
            if (aLe === '+Inf') return 1
            if (bLe === '+Inf') return -1
            return parseFloat(aLe) - parseFloat(bLe)
          }),
          sum,
          count
        })
        buckets.forEach(b => processed.add(b.labels?.metric || ''))
        if (sum) processed.add(sum.labels?.metric || '')
        if (count) processed.add(count.labels?.metric || '')
      }
    } else if (!metricName.includes('_sum') && !metricName.includes('_count')) {
      // Regular metric (counter, gauge, etc.)
      groups.push({
        name: metricName,
        type: metricName.includes('_total') ? 'counter' : 'gauge',
        buckets: [metric]
      })
      processed.add(metricName)
    }
  }

  return groups.sort((a, b) => a.name.localeCompare(b.name))
})

// Time range controls
const timeRange = ref('1h')
const customStartTime = ref('')
const customEndTime = ref('')

// Query controls
const aggregation = ref('none')
const bucketSize = ref('30000')
const chartType = ref('line')

// Computed properties
const summaryStats = computed(() => {
  if (!metricsData.value.length) return []

  const totalSeries = metricsData.value.length
  const totalDataPoints = metricsData.value.reduce((sum, series) => sum + series.samples.length, 0)
  const latestTimestamp = Math.max(...metricsData.value.flatMap(series =>
    series.samples.map(sample => sample[0])
  ))
  const timeSpan = latestTimestamp - Math.min(...metricsData.value.flatMap(series =>
    series.samples.map(sample => sample[0])
  ))

  return [
    {
      label: 'Total Series',
      value: totalSeries.toLocaleString(),
      icon: 'lucide:layers'
    },
    {
      label: 'Data Points',
      value: totalDataPoints.toLocaleString(),
      icon: 'lucide:database'
    },
    {
      label: 'Time Span',
      value: formatDuration(timeSpan),
      icon: 'lucide:clock'
    },
    {
      label: 'Latest Update',
      value: formatTimestamp(latestTimestamp),
      icon: 'lucide:calendar'
    }
  ]
})

// Methods
const updateTimeRange = () => {
  if (timeRange.value === 'custom') {
    // Set default custom range to last hour
    const now = new Date()
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000)

    customEndTime.value = now.toISOString().slice(0, 16)
    customStartTime.value = oneHourAgo.toISOString().slice(0, 16)
  }
}

const updateCustomTimeRange = () => {
  if (customStartTime.value && customEndTime.value) {
    loadMetrics()
  }
}

const updateRefreshInterval = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }

  const interval = parseInt(refreshInterval.value)
  if (interval > 0) {
    refreshTimer.value = setInterval(() => {
      loadMetrics()
    }, interval * 1000)
  }
}

const getTimeRangeMs = () => {
  const now = Date.now()

  switch (timeRange.value) {
    case '5m': return { start: now - 5 * 60 * 1000, end: now }
    case '15m': return { start: now - 15 * 60 * 1000, end: now }
    case '1h': return { start: now - 60 * 60 * 1000, end: now }
    case '6h': return { start: now - 6 * 60 * 60 * 1000, end: now }
    case '24h': return { start: now - 24 * 60 * 60 * 1000, end: now }
    case '7d': return { start: now - 7 * 24 * 60 * 60 * 1000, end: now }
    case 'custom':
      if (customStartTime.value && customEndTime.value) {
        return {
          start: new Date(customStartTime.value).getTime(),
          end: new Date(customEndTime.value).getTime()
        }
      }
      return { start: now - 60 * 60 * 1000, end: now }
    default:
      return { start: now - 60 * 60 * 1000, end: now }
  }
}

const loadAvailableMetrics = async () => {
  try {
    console.log('Loading available metrics from:', `${apiBase}/api/metrics/keys?limit=100`)
    const response = await fetch(`${apiBase}/api/metrics/keys?limit=100`)
    console.log('Response status:', response.status, response.statusText)

    if (!response.ok) {
      throw new Error(`Failed to load metrics: ${response.statusText}`)
    }

    const data = await response.json()
    console.log('Received data:', data)
    availableMetrics.value = data.keys || []
    console.log('Available metrics count:', availableMetrics.value.length)
    console.log('First few metrics:', availableMetrics.value.slice(0, 3))
  } catch (err) {
    console.error('Error loading metrics:', err)
    error.value = err instanceof Error ? err.message : 'Failed to load available metrics'
  }
}

const toggleMetric = (metricKey: string) => {
  const index = selectedMetrics.value.indexOf(metricKey)
  if (index > -1) {
    selectedMetrics.value.splice(index, 1)
    console.log('Removed metric:', metricKey, 'Selected:', selectedMetrics.value)
  } else {
    selectedMetrics.value.push(metricKey)
    console.log('Added metric:', metricKey, 'Selected:', selectedMetrics.value)
  }
}

const isGroupSelected = (group: HistogramGroup) => {
  return group.buckets.some(bucket => selectedMetrics.value.includes(bucket.key))
}

const toggleGroup = (group: HistogramGroup) => {
  const isSelected = isGroupSelected(group)

  if (isSelected) {
    // Remove all metrics in this group
    group.buckets.forEach(bucket => {
      const index = selectedMetrics.value.indexOf(bucket.key)
      if (index > -1) {
        selectedMetrics.value.splice(index, 1)
      }
    })
    if (group.sum) {
      const index = selectedMetrics.value.indexOf(group.sum.key)
      if (index > -1) {
        selectedMetrics.value.splice(index, 1)
      }
    }
    if (group.count) {
      const index = selectedMetrics.value.indexOf(group.count.key)
      if (index > -1) {
        selectedMetrics.value.splice(index, 1)
      }
    }
  } else {
    // Add all metrics in this group
    group.buckets.forEach(bucket => {
      if (!selectedMetrics.value.includes(bucket.key)) {
        selectedMetrics.value.push(bucket.key)
      }
    })
    if (group.sum && !selectedMetrics.value.includes(group.sum.key)) {
      selectedMetrics.value.push(group.sum.key)
    }
    if (group.count && !selectedMetrics.value.includes(group.count.key)) {
      selectedMetrics.value.push(group.count.key)
    }
  }

  console.log('Toggled group:', group.name, 'Selected:', selectedMetrics.value)
}

const getBucketLabel = (metricKey: string, index: number) => {
  // Since we can't easily extract the le value from the Redis key,
  // let's show a more meaningful label based on the bucket index
  // This gives users an idea of the bucket distribution

  const bucketLabels = [
    '≤1.0', '≤2.0', '≤5.0', '≤10.0', '≤20.0', '≤50.0',
    '≤100.0', '≤200.0', '≤500.0', '≤1000.0', '≤2000.0',
    '≤5000.0', '≤10000.0', '≤20000.0', '+Inf'
  ]

  if (index < bucketLabels.length) {
    return bucketLabels[index]
  }

  // Fallback: show index-based label
  return `≤${(index + 1) * 10}`
}

const loadMetrics = async () => {
  if (loading.value || !selectedMetrics.value.length) return

  console.log('Loading metrics for selected:', selectedMetrics.value)
  loading.value = true
  error.value = ''

  try {
    const { start, end } = getTimeRangeMs()
    console.log('Time range:', { start, end })
    const allMetricsData: MetricSeries[] = []

    // Load data for each selected metric
    for (const metricKey of selectedMetrics.value) {
      const metric = availableMetrics.value.find(m => m.key === metricKey)
      if (!metric) {
        console.log('Metric not found for key:', metricKey)
        continue
      }

      const metricName = metric.labels.metric || metricKey
      console.log('Loading metric:', metricName, 'from key:', metricKey)

      const params = new URLSearchParams({
        metric: metricName,
        start: start.toString(),
        end: end.toString(),
        limit: '1000'
      })

      if (aggregation.value !== 'none') {
        params.append('agg', aggregation.value)
        params.append('bucket_ms', bucketSize.value)
      }

      // Add label filters
      const labelFilters: string[] = []
      Object.entries(metric.labels).forEach(([key, value]) => {
        if (key !== 'metric') {
          labelFilters.push(`${key}=${value}`)
        }
      })

      if (labelFilters.length > 0) {
        params.append('labels', labelFilters.join(','))
      }

      const url = `${apiBase}/api/metrics/query?${params}`
      console.log('Fetching URL:', url)

      const response = await fetch(url)
      console.log('Response status:', response.status, response.statusText)

      if (!response.ok) {
        throw new Error(`Failed to load metric ${metricName}: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('Received data for', metricName, ':', data)
      allMetricsData.push(...data.series)
    }

    metricsData.value = allMetricsData
    console.log('Total metrics data loaded:', allMetricsData.length, 'series')
    console.log('Final metricsData:', metricsData.value)
  } catch (err) {
    console.error('Error loading metrics:', err)
    error.value = err instanceof Error ? err.message : 'Failed to load metrics'
  } finally {
    loading.value = false
  }
}

const getChartData = (metricKey: string) => {
  // Find the metric from available metrics
  const metric = availableMetrics.value.find(m => m.key === metricKey)
  if (!metric) {
    console.log('Metric not found for key:', metricKey)
    return []
  }

  // Find the corresponding series data
  const series = metricsData.value.find(s => s.key === metricKey)
  if (!series) {
    console.log('Series data not found for key:', metricKey)
    return []
  }

  console.log('Found series data for', metricKey, ':', series.samples.length, 'samples')

  // Convert to chart format
  const chartData = series.samples.map(([timestamp, value], index) => ({
    timestamp: new Date(timestamp).toISOString(),
    value: typeof value === 'string' ? parseFloat(value) : value,
    index: index
  }))

  console.log('Chart data for', metricKey, ':', chartData.length, 'points')
  return chartData
}

const getMetricDisplayName = (metricKey: string) => {
  const metric = availableMetrics.value.find(m => m.key === metricKey)
  return metric?.labels.metric || metricKey
}

const getChartTypeForMetric = (metricKey: string) => {
  const metric = availableMetrics.value.find(m => m.key === metricKey)
  const metricName = metric?.labels.metric || metricKey

  // Check if this is a histogram metric
  if (metricName.includes('_bucket') || metricName.includes('histogram')) {
    return 'histogram'
  }

  // Default to the selected chart type for non-histogram metrics
  return chartType.value
}

const getMetricType = (metricKey: string) => {
  const metric = availableMetrics.value.find(m => m.key === metricKey)
  const metricName = metric?.labels.metric || metricKey

  if (metricName.includes('_bucket')) return 'Histogram Bucket'
  if (metricName.includes('_sum')) return 'Histogram Sum'
  if (metricName.includes('_count')) return 'Counter'
  if (metricName.includes('total')) return 'Counter'
  if (metricName.includes('usage') || metricName.includes('running') || metricName.includes('waiting')) return 'Gauge'
  return 'Metric'
}

const getMetricDescription = (metricKey: string) => {
  const metric = availableMetrics.value.find(m => m.key === metricKey)
  const metricName = metric?.labels.metric || metricKey

  // Add comprehensive descriptions for common metrics
  if (metricName.includes('prompt_tokens')) return 'Number of input tokens processed by the model. Higher values indicate longer prompts or more complex inputs.'
  if (metricName.includes('generation_tokens')) return 'Number of output tokens generated by the model. Indicates response length and generation complexity.'
  if (metricName.includes('time_to_first_token')) return 'Latency from request start to first token generation. Critical for user experience and perceived performance.'
  if (metricName.includes('e2e_request_latency')) return 'Total end-to-end request processing time including queue, processing, and response delivery.'
  if (metricName.includes('requests_running')) return 'Current number of active requests being processed. Indicates system load and concurrency.'
  if (metricName.includes('requests_waiting')) return 'Number of requests queued and waiting for processing. High values indicate system overload.'
  if (metricName.includes('cache_hit')) return 'Cache hit ratio (0-1). Higher values indicate better cache efficiency and reduced computation.'
  if (metricName.includes('memory_usage')) return 'Memory utilization percentage. Critical for system stability and performance optimization.'
  if (metricName.includes('gpu_utilization')) return 'GPU usage percentage. Indicates hardware efficiency and potential bottlenecks.'
  if (metricName.includes('throughput')) return 'Requests processed per second. Key performance indicator for system capacity.'
  if (metricName.includes('queue_time')) return 'Average time requests spend waiting in queue before processing begins.'
  if (metricName.includes('processing_time')) return 'Time spent actively processing requests (excluding queue and I/O time).'
  if (metricName.includes('error_rate')) return 'Percentage of failed requests. Critical reliability metric for system health.'
  if (metricName.includes('response_time')) return 'Average time from request to complete response delivery.'
  if (metricName.includes('concurrent_requests')) return 'Maximum concurrent requests handled simultaneously.'
  if (metricName.includes('batch_size')) return 'Average number of requests processed in each batch for efficiency.'
  if (metricName.includes('model_load_time')) return 'Time required to load and initialize the model. Affects startup performance.'
  if (metricName.includes('warmup_time')) return 'Time needed for model to reach optimal performance after loading.'
  if (metricName.includes('idle_time')) return 'Time spent waiting for new requests. Indicates system utilization efficiency.'
  if (metricName.includes('active_time')) return 'Time spent actively processing requests vs. idle time.'

  return 'LLM performance metric data'
}

const formatTimestamp = (timestamp: number) => {
  return new Date(timestamp).toLocaleString()
}

const formatDuration = (ms: number) => {
  const seconds = Math.floor(ms / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) return `${days}d ${hours % 24}h`
  if (hours > 0) return `${hours}h ${minutes % 60}m`
  if (minutes > 0) return `${minutes}m ${seconds % 60}s`
  return `${seconds}s`
}

const getChartMetadata = (metricKey: string) => {
  const chartData = getChartData(metricKey)
  const metric = availableMetrics.value.find(m => m.key === metricKey)
  const metricName = metric?.labels?.metric || metricKey

  if (!chartData || chartData.length === 0) {
    return 'No data available for the selected time range'
  }

  // Calculate statistics
  const values = chartData.map(d => d.value)
  const latestValue = values[values.length - 1]
  const minValue = Math.min(...values)
  const maxValue = Math.max(...values)
  const avgValue = values.reduce((sum, val) => sum + val, 0) / values.length

  // Time range info
  const startTime = new Date(chartData[0]?.timestamp || 0)
  const endTime = new Date(chartData[chartData.length - 1]?.timestamp || 0)
  const timeRange = `${startTime.toLocaleTimeString()} - ${endTime.toLocaleTimeString()}`

  // Data freshness
  const now = new Date()
  const lastUpdate = new Date(chartData[chartData.length - 1]?.timestamp || 0)
  const minutesAgo = Math.floor((now.getTime() - lastUpdate.getTime()) / (1000 * 60))

  // Format values based on metric type
  const formatValue = (val: number) => {
    if (metricName.includes('time') || metricName.includes('latency')) {
      return val >= 1000 ? `${(val / 1000).toFixed(1)}s` : `${val.toFixed(1)}ms`
    } else if (metricName.includes('token')) {
      return val >= 1000000 ? `${(val / 1000000).toFixed(1)}M` :
             val >= 1000 ? `${(val / 1000).toFixed(1)}K` : val.toFixed(0)
    } else if (metricName.includes('usage') || metricName.includes('ratio')) {
      return val <= 1 ? `${(val * 100).toFixed(1)}%` : val.toFixed(2)
    }
    return val.toFixed(2)
  }

  // Build metadata string
  const metadata = [
    `📊 ${chartData.length} data points`,
    `📅 ${timeRange}`,
    `📈 Latest: ${formatValue(latestValue || 0)}`,
    `📉 Range: ${formatValue(minValue)} - ${formatValue(maxValue)}`,
    `📊 Avg: ${formatValue(avgValue)}`,
    `🔄 Agg: ${aggregation.value}`,
    Number(bucketSize.value || 0) > 0 ? `⏱️ Bucket: ${bucketSize.value || 0}s` : '',
    `🕒 Updated: ${minutesAgo}m ago`
  ].filter(Boolean).join(' • ')

  return metadata
}

const exportData = () => {
  const data = {
    timestamp: new Date().toISOString(),
    timeRange: timeRange.value,
    aggregation: aggregation.value,
    bucketSize: bucketSize.value,
    metrics: metricsData.value
  }

  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `metrics-export-${new Date().toISOString().slice(0, 19)}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const clearData = () => {
  metricsData.value = []
  selectedMetrics.value = []
}

// Lifecycle
onMounted(() => {
  console.log('Component mounted, loading available metrics...')
  // Only load metrics on client side
  if (typeof window !== 'undefined') {
    loadAvailableMetrics()
  }
  updateTimeRange()
  updateRefreshInterval()
})

onUnmounted(() => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
  }
})

// Watch for changes
watch(selectedMetrics, () => {
  if (selectedMetrics.value.length > 0) {
    loadMetrics()
  }
})
</script>
