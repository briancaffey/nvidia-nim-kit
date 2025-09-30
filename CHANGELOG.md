# Changelog

## [1.6.0](https://github.com/briancaffey/nvidia-nim-kit/compare/v1.5.0...v1.6.0) (2025-09-30)


### Features

* **readme:** update readme and contributing.md ([af70fac](https://github.com/briancaffey/nvidia-nim-kit/commit/af70facb4a8641888926db3984186a21324be4da))


### Bug Fixes

* **logo:** fix logo and home page ([26ff5e6](https://github.com/briancaffey/nvidia-nim-kit/commit/26ff5e6b9409a89cac2c7c62fe16ea9f0c3496e7))

## [1.5.0](https://github.com/briancaffey/nvidia-nim-kit/compare/v1.4.0...v1.5.0) (2025-09-29)


### Features

* **asr:** improve output visualization for asr nim ([0a8a1d6](https://github.com/briancaffey/nvidia-nim-kit/commit/0a8a1d677cc5e75f2c9c455994ba8cf97991debd))
* **llm:** refactor llm components ([b061531](https://github.com/briancaffey/nvidia-nim-kit/commit/b0615311cee72b6d2bc7fc9711d60440f15da284))
* **nvext:** add support for nvext parameters in llm interface ([ae5aa82](https://github.com/briancaffey/nvidia-nim-kit/commit/ae5aa82be0d7b3d49804de01f7580de5cdf0d3c3))
* **observability:** add prometheus metrics collection and grafana dashboards for nim metrics ([41f3045](https://github.com/briancaffey/nvidia-nim-kit/commit/41f30454429e61ec52cdf86f5be11f52dad13eec))
* **paddleocr:** add support for baidu paddleocr inference ([ae9f2a6](https://github.com/briancaffey/nvidia-nim-kit/commit/ae9f2a66858f6f4acdb7538e3f7f2627fc4dad49))


### Bug Fixes

* **config:** refactor nim config form and add nim config form to nim page ([91eab31](https://github.com/briancaffey/nvidia-nim-kit/commit/91eab318d53439e61beea1192f925f37fd667bb8))
* **image:** fix flux kontext dev image generation ([47a0ac1](https://github.com/briancaffey/nvidia-nim-kit/commit/47a0ac1f39110b5fa886b42c1eb6a7156e767b4e))
* **llm:** fix model name issue with llm nims ([0247d61](https://github.com/briancaffey/nvidia-nim-kit/commit/0247d61174f987920a32b7bcb443c1c5cd066f38))
* **llm:** remove unused frontend code ([c02fd5c](https://github.com/briancaffey/nvidia-nim-kit/commit/c02fd5c6789f2ae4fff6cb9da0b307579d8c893e))
* **logo:** update logo ([e9a50e4](https://github.com/briancaffey/nvidia-nim-kit/commit/e9a50e4e717158ae9febe767a920b7e145ef4b24))
* **metrics:** remove backend and frontend metrics code, using prometheus and grafana instead ([e7d83a8](https://github.com/briancaffey/nvidia-nim-kit/commit/e7d83a846339f918e173ee7806293662f4f75f4f))
* **misc:** fix issues with paddleocr and flux ui ([8c4187a](https://github.com/briancaffey/nvidia-nim-kit/commit/8c4187a19288e420aed3e5cbb5ec1c9d7bcaa10e))

## [1.4.0](https://github.com/briancaffey/nvidia-nim-kit/compare/v1.3.0...v1.4.0) (2025-09-24)


### Features

* **studiovoice:** add support for local and remote inference with nvidia studiovoice nim ([d5156cb](https://github.com/briancaffey/nvidia-nim-kit/commit/d5156cb7276da500a814d39dfaf40944c196cb0d))


### Bug Fixes

* **nuxt:** fix nuxt warnings ([62ac541](https://github.com/briancaffey/nvidia-nim-kit/commit/62ac5410008ef672d30f626534e1aff56a6b5d7f))

## [1.3.0](https://github.com/briancaffey/nvidia-nim-kit/compare/v1.2.0...v1.3.0) (2025-09-24)


### Features

* **asr:** add support for local and cloud asr inference with parakeet nim ([1e8ee72](https://github.com/briancaffey/nvidia-nim-kit/commit/1e8ee7237b99958de45f9a2843b214d891073492))
* **image:** add support for flux dev canny and depth map modes ([4b870b6](https://github.com/briancaffey/nvidia-nim-kit/commit/4b870b62160643e0e6b7c05096731e2d30f7fea4))
* **llm:** completion and chat with streaming and non-streaming and support for logprobs ([ee10453](https://github.com/briancaffey/nvidia-nim-kit/commit/ee104531e28eccd29072ac169d9d79673dd32915))
* **metrics:** wip llm metrics dashboard and redis timeseries ([568bcd5](https://github.com/briancaffey/nvidia-nim-kit/commit/568bcd5abc1c81abaffaf5cfcc1db4ab59c6b78e))
* **nims:** add local nims catalog ([1527920](https://github.com/briancaffey/nvidia-nim-kit/commit/1527920201816d6ba780a9da6af0704624b67773))
* **nvapi:** initial support for adding NVIDIA_API_KEY to backend application to use nvidia cloud inference services on build.nvidia.com ([a213bd6](https://github.com/briancaffey/nvidia-nim-kit/commit/a213bd60a746371b8055e1381f20de7b125a84ab))
* **schnell:** basic implentation for schnell image generation ([2a72ff7](https://github.com/briancaffey/nvidia-nim-kit/commit/2a72ff72f2466b232b44eb42727996af510acae8))
* **trellis:** add support for generating 3d models with trellis nim ([0e578c2](https://github.com/briancaffey/nvidia-nim-kit/commit/0e578c25522d73a10492402fd8c7c608e880b1a2))
* **tresjs:** add tresjs for 3d model viewing with rtx 5090 sample model ([b74b4c7](https://github.com/briancaffey/nvidia-nim-kit/commit/b74b4c7b7f954b22cc692b525964d4b3711ef159))


### Bug Fixes

* **dev:** fixes for setting up dev environment on fresh linux environment ([e09eb72](https://github.com/briancaffey/nvidia-nim-kit/commit/e09eb7238c72764a7aa8860400561d38952057b5))
* **docker:** fixes for docker and docker compose ([10b31de](https://github.com/briancaffey/nvidia-nim-kit/commit/10b31de0112ddf21094e91dca5aa9849f9de2798))
* **nvapi:** fixes for supporting nvidia cloud generation in llm and image generation forms ([e8760fe](https://github.com/briancaffey/nvidia-nim-kit/commit/e8760fe74ce93cc941c8442611e5c2c34444ba37))

## [1.2.0](https://github.com/briancaffey/nvidia-nim-kit/compare/v1.1.0...v1.2.0) (2025-09-18)


### Features

* **frontend:** add nuxt frontend for nim kit with sample pages ([0ab2a80](https://github.com/briancaffey/nvidia-nim-kit/commit/0ab2a802c166a375a86b7eedcc4db4216b2811c6))

## [1.1.0](https://github.com/briancaffey/nvidia-nim-kit/compare/v1.0.0...v1.1.0) (2025-09-18)


### Features

* **celery:** add celery, beat, flower ([f8bd02e](https://github.com/briancaffey/nvidia-nim-kit/commit/f8bd02e890fbf1837351c216411074f5350f48f9))
* **fastapi:** add fastapi and tests ([aa7ce82](https://github.com/briancaffey/nvidia-nim-kit/commit/aa7ce82ebd2421b47dde7d30db159df1d8c340d2))

## 1.0.0 (2025-09-17)


### Features

* **release-please:** add release please ([8e18dbe](https://github.com/briancaffey/nvidia-nim-kit/commit/8e18dbe25663fedaace913f542f6ce61405cabb5))
