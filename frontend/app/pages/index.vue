<template>
  <div class="container mx-auto px-4 py-8">
    <!-- Hero Section -->
    <section class="text-center py-16">
      <div class="max-w-3xl mx-auto">
        <div class="flex justify-center mb-8">
          <Logo width="100" height="100" />
        </div>
        <h1 class="text-4xl font-bold tracking-tight sm:text-6xl mb-6">
          Welcome to <span class="text-primary">NIM Kit</span>
        </h1>
        <p class="text-xl text-muted-foreground mb-8">
          A powerful toolkit for building modern applications with NVIDIA's cutting-edge technology.
        </p>
        <div class="flex flex-col sm:flex-row gap-4 justify-center">
          <Button size="lg" class="text-lg px-8">
            Get Started
            <Icon name="lucide:arrow-right" class="ml-2 h-5 w-5" />
          </Button>
          <NuxtLink to="/about">
            <Button variant="outline" size="lg" class="text-lg px-8">
              Learn More
            </Button>
          </NuxtLink>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="py-16">
      <div class="text-center mb-12">
        <h2 class="text-3xl font-bold tracking-tight mb-4">Key Features</h2>
        <p class="text-lg text-muted-foreground">
          Everything you need to build amazing applications
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        <Card class="p-6">
          <CardHeader>
            <div class="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
              <Icon name="lucide:zap" class="h-6 w-6 text-primary" />
            </div>
            <CardTitle>High Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <p class="text-muted-foreground">
              Leverage NVIDIA's powerful hardware acceleration for lightning-fast processing and rendering.
            </p>
          </CardContent>
        </Card>

        <Card class="p-6">
          <CardHeader>
            <div class="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
              <Icon name="lucide:shield" class="h-6 w-6 text-primary" />
            </div>
            <CardTitle>Enterprise Ready</CardTitle>
          </CardHeader>
          <CardContent>
            <p class="text-muted-foreground">
              Built with enterprise-grade security and reliability for mission-critical applications.
            </p>
          </CardContent>
        </Card>

        <Card class="p-6">
          <CardHeader>
            <div class="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
              <Icon name="lucide:code" class="h-6 w-6 text-primary" />
            </div>
            <CardTitle>Developer Friendly</CardTitle>
          </CardHeader>
          <CardContent>
            <p class="text-muted-foreground">
              Comprehensive APIs and documentation to help developers build amazing experiences.
            </p>
          </CardContent>
        </Card>

        <Card class="p-6">
          <CardHeader>
            <div class="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
              <Icon name="lucide:cloud" class="h-6 w-6 text-primary" />
            </div>
            <CardTitle>Cloud Native</CardTitle>
          </CardHeader>
          <CardContent>
            <p class="text-muted-foreground">
              Seamlessly deploy and scale your applications across cloud platforms and edge devices.
            </p>
          </CardContent>
        </Card>

        <Card class="p-6">
          <CardHeader>
            <div class="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
              <Icon name="lucide:brain" class="h-6 w-6 text-primary" />
            </div>
            <CardTitle>AI Powered</CardTitle>
          </CardHeader>
          <CardContent>
            <p class="text-muted-foreground">
              Integrate advanced AI capabilities with pre-trained models and custom training pipelines.
            </p>
          </CardContent>
        </Card>

        <Card class="p-6">
          <CardHeader>
            <div class="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
              <Icon name="lucide:users" class="h-6 w-6 text-primary" />
            </div>
            <CardTitle>Community Driven</CardTitle>
          </CardHeader>
          <CardContent>
            <p class="text-muted-foreground">
              Join a vibrant community of developers, researchers, and innovators pushing boundaries.
            </p>
          </CardContent>
        </Card>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="py-16">
      <Card class="p-8 text-center">
        <CardHeader>
          <CardTitle class="text-2xl mb-4">Ready to Get Started?</CardTitle>
          <CardDescription class="text-lg">
            Join thousands of developers who are already building the future with NIM Kit.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div class="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" class="text-lg px-8">
              Start Building
              <Icon name="lucide:rocket" class="ml-2 h-5 w-5" />
            </Button>
            <NuxtLink to="/about">
              <Button variant="outline" size="lg" class="text-lg px-8">
                Learn More About NIM Kit
              </Button>
            </NuxtLink>
          </div>
        </CardContent>
      </Card>
    </section>
  </div>
</template>

<!-- <script setup lang="ts">
// Set page metadata
// useHead({
//   title: 'Home - NIM Kit',
//   meta: [
//     { name: 'description', content: 'Welcome to NIM Kit - A powerful toolkit for building modern applications with NVIDIA\'s cutting-edge technology.' }
//   ]
// })
</script> -->
