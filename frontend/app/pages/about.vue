<template>
  <div class="container mx-auto px-4 py-8 max-w-4xl">
    <div class="mb-8">
      <h1 class="text-4xl font-bold mb-4">About NIM Kit</h1>
      <p class="text-xl text-muted-foreground mb-6">
        A developer-focused platform for exploring NVIDIA NIMs locally, with galleries for viewing results and convenient utilities for audio processing, metrics visualization, and more.
      </p>
    </div>

    <div class="space-y-8">
      <!-- Highlighted Comparison -->
      <section class="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/50 dark:to-purple-950/50 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
        <div class="text-center">
          <div class="text-3xl mb-3">🏠</div>
          <h2 class="text-2xl font-bold mb-3 text-blue-900 dark:text-blue-100">
            Think of it as a local version of
            <a href="https://build.nvidia.com" target="_blank" rel="noopener noreferrer"
               class="underline hover:text-blue-700 dark:hover:text-blue-300 transition-colors">
              build.nvidia.com
            </a>
          </h2>
        </div>
      </section>

      <!-- Core Purpose -->
      <section>
        <h2 class="text-2xl font-semibold mb-4">What is NIM Kit?</h2>
        <p class="text-muted-foreground mb-4">
          NIM Kit is a developer exploration platform designed to help you discover and experiment with NVIDIA NIMs
          (NVIDIA Inference Microservices) running locally on your RTX hardware. It provides galleries to view
          inference results alongside input data, and includes convenient utilities for common development tasks.
        </p>
        <div class="grid md:grid-cols-2 gap-4">
          <div class="p-4 border rounded-lg">
            <h3 class="font-semibold mb-2">🎯 Core Features</h3>
            <ul class="text-sm text-muted-foreground space-y-1">
              <li>• Gallery for viewing inference results with input data</li>
              <li>• Audio sample rate conversion utilities</li>
              <li>• Metrics visualization and analysis tools</li>
              <li>• Easy NIM configuration and management</li>
              <li>• Developer-friendly exploration interface</li>
            </ul>
          </div>
          <div class="p-4 border rounded-lg">
            <h3 class="font-semibold mb-2">🚀 Benefits</h3>
            <ul class="text-sm text-muted-foreground space-y-1">
              <li>• Explore NIM capabilities without cloud dependencies</li>
              <li>• Visualize results and compare different models</li>
              <li>• Streamlined audio and data processing workflows</li>
              <li>• Local development and experimentation</li>
              <li>• Open-source and community-driven</li>
            </ul>
          </div>
        </div>
      </section>

      <!-- RTX Support -->
      <section>
        <h2 class="text-2xl font-semibold mb-4">RTX-Powered AI Capabilities</h2>
        <p class="text-muted-foreground mb-4">
          Explore the full spectrum of NVIDIA RTX-powered NIMs locally, with galleries to view results and
          utilities to process the diverse range of AI modalities available on your hardware.
        </p>
        <div class="grid md:grid-cols-3 gap-4">
          <div class="p-4 border rounded-lg text-center">
            <div class="text-2xl mb-2">🤖</div>
            <h3 class="font-semibold mb-2">Large Language Models</h3>
            <p class="text-sm text-muted-foreground">Advanced text generation, conversation, and reasoning capabilities</p>
          </div>
          <div class="p-4 border rounded-lg text-center">
            <div class="text-2xl mb-2">🎨</div>
            <h3 class="font-semibold mb-2">Image Generation</h3>
            <p class="text-sm text-muted-foreground">Create stunning visuals from text prompts and image-to-image transformations</p>
          </div>
          <div class="p-4 border rounded-lg text-center">
            <div class="text-2xl mb-2">🎵</div>
            <h3 class="font-semibold mb-2">Voice & Audio</h3>
            <p class="text-sm text-muted-foreground">Text-to-speech, voice cloning, and audio processing capabilities</p>
          </div>
          <div class="p-4 border rounded-lg text-center">
            <div class="text-2xl mb-2">🎮</div>
            <h3 class="font-semibold mb-2">3D Model Generation</h3>
            <p class="text-sm text-muted-foreground">Generate and manipulate 3D models for games, VR, and visualization</p>
          </div>
          <div class="p-4 border rounded-lg text-center">
            <div class="text-2xl mb-2">📊</div>
            <h3 class="font-semibold mb-2">Data Processing</h3>
            <p class="text-sm text-muted-foreground">Advanced data analysis, visualization, and insights generation</p>
          </div>
          <div class="p-4 border rounded-lg text-center">
            <div class="text-2xl mb-2">🔬</div>
            <h3 class="font-semibold mb-2">Research Tools</h3>
            <p class="text-sm text-muted-foreground">Specialized tools for scientific computing and research applications</p>
          </div>
        </div>
      </section>

      <!-- Resources & Support -->
      <section>
        <h2 class="text-2xl font-semibold mb-4">Developer Resources</h2>
        <p class="text-muted-foreground mb-4">
          NIM Kit provides the tools and resources developers need to explore NIM capabilities,
          view results in galleries, and utilize convenient processing utilities.
        </p>
        <div class="grid md:grid-cols-2 gap-6">
          <div class="space-y-4">
            <div class="p-4 border rounded-lg">
              <h3 class="font-semibold mb-2">📚 Example Data & Templates</h3>
              <p class="text-sm text-muted-foreground">
                Sample datasets and example configurations to help you explore different NIM capabilities and use cases.
              </p>
            </div>
            <div class="p-4 border rounded-lg">
              <h3 class="font-semibold mb-2">💡 Tips & Best Practices</h3>
              <p class="text-sm text-muted-foreground">
                Guidance for exploring NIM capabilities, optimizing local performance, and using utilities effectively.
              </p>
            </div>
          </div>
          <div class="space-y-4">
            <div class="p-4 border rounded-lg">
              <h3 class="font-semibold mb-2">🔗 Documentation Links</h3>
              <p class="text-sm text-muted-foreground">
                Guides for setting up NIMs, using galleries, and leveraging utilities for your development workflow.
              </p>
            </div>
            <div class="p-4 border rounded-lg">
              <h3 class="font-semibold mb-2">⚙️ Easy Configuration</h3>
              <p class="text-sm text-muted-foreground">
                Simple setup and configuration tools to get NIMs running locally for exploration and development.
              </p>
            </div>
          </div>
        </div>
      </section>

      <!-- Getting Started -->
      <section class="bg-muted/50 p-6 rounded-lg">
        <h2 class="text-2xl font-semibold mb-4">Ready to Explore?</h2>
        <p class="text-muted-foreground mb-4">
          Whether you're a developer exploring AI capabilities, a researcher experimenting with different models,
          or someone curious about local AI inference, NIM Kit provides the tools and galleries you need to discover what's possible.
        </p>
        <div class="flex flex-wrap gap-3">
          <button class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors">
            Explore Documentation
          </button>
          <button class="px-4 py-2 border border-border rounded-md hover:bg-muted transition-colors">
            View Examples
          </button>
          <button class="px-4 py-2 border border-border rounded-md hover:bg-muted transition-colors">
            Join Community
          </button>
        </div>
      </section>
    </div>
  </div>
</template>
